using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Windows.Threading;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.Colors;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Geometry;
using Autodesk.AutoCAD.Runtime;
using AcadApp = Autodesk.AutoCAD.ApplicationServices.Application;
using AcadException = Autodesk.AutoCAD.Runtime.Exception;

[assembly: ExtensionApplication(typeof(Agy.AutoCadBridge.AutoCadBridgeApp))]
[assembly: CommandClass(typeof(Agy.AutoCadBridge.AutoCadBridgeApp))]

namespace Agy.AutoCadBridge;

public sealed class AutoCadBridgeApp : IExtensionApplication
{
    public const string PipeName = "agy-autocad-direct";
    private static readonly Encoding Utf8NoBom = new UTF8Encoding(false);
    private static readonly object LispLock = new();
    private static TaskCompletionSource<string>? _lispTcs;

    private Dispatcher? _uiDispatcher;
    private CancellationTokenSource? _cts;
    private Task? _serverTask;

    public void Initialize()
    {
        _uiDispatcher = Dispatcher.CurrentDispatcher;
        _cts = new CancellationTokenSource();
        _serverTask = Task.Run(() => RunPipeServerLoopAsync(_cts.Token));
    }

    public void Terminate()
    {
        _cts?.Cancel();
    }

    [LispFunction("agy_rpc_done")]
    public static ResultBuffer AgyRpcDone(ResultBuffer args)
    {
        string payload = "OK|";
        if (args != null)
        {
            var vals = args.AsArray();
            if (vals.Length > 0 && vals[0].Value != null)
            {
                payload = vals[0].Value.ToString() ?? "OK|";
            }
        }
        _lispTcs?.TrySetResult(payload);
        return new ResultBuffer(new TypedValue((int)LispDataType.Text, "OK"));
    }

    private async Task RunPipeServerLoopAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                await using var server = new NamedPipeServerStream(
                    PipeName,
                    PipeDirection.InOut,
                    4,
                    PipeTransmissionMode.Byte,
                    PipeOptions.Asynchronous);

                await server.WaitForConnectionAsync(ct).ConfigureAwait(false);
                using var reader = new StreamReader(server, Utf8NoBom, false, 65536, leaveOpen: true);
                await using var writer = new StreamWriter(server, Utf8NoBom, 65536, leaveOpen: true) { AutoFlush = true };

                string? line = await reader.ReadLineAsync(ct).ConfigureAwait(false);
                if (string.IsNullOrWhiteSpace(line))
                    continue;

                JsonNode? reqNode = JsonNode.Parse(line);
                string reqId = reqNode?["id"]?.GetValue<string>() ?? "";
                string method = reqNode?["method"]?.GetValue<string>() ?? "";
                JsonObject parms = reqNode?["params"]?.AsObject() ?? new JsonObject();

                JsonObject resp;
                try
                {
                    JsonNode? result = await DispatchAsync(method, parms, ct).ConfigureAwait(false);
                    resp = new JsonObject
                    {
                        ["id"] = reqId,
                        ["ok"] = true,
                        ["result"] = result
                    };
                }
                catch (System.Exception ex)
                {
                    resp = new JsonObject
                    {
                        ["id"] = reqId,
                        ["ok"] = false,
                        ["error"] = $"{ex.Message} [{ex.GetType().Name}] @ {ex.StackTrace}"
                    };
                }

                await writer.WriteLineAsync(resp.ToJsonString()).ConfigureAwait(false);
                await writer.FlushAsync(ct).ConfigureAwait(false);
                server.WaitForPipeDrain();
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch
            {
                await Task.Delay(100, ct).ConfigureAwait(false);
            }
        }
    }

    private async Task<JsonNode?> DispatchAsync(string method, JsonObject parms, CancellationToken ct)
    {
        if (_uiDispatcher == null)
            throw new InvalidOperationException("AutoCAD UI Dispatcher not initialized.");

        if (method == "eval_lisp")
        {
            string expr = parms["expr"]?.GetValue<string>() ?? "";
            int timeoutMs = parms["timeout_ms"]?.GetValue<int>() ?? 35000;
            return await EvalLispAsync(expr, timeoutMs, ct).ConfigureAwait(false);
        }

        if (method == "send_command")
        {
            string cmd = parms["command"]?.GetValue<string>() ?? "";
            return await _uiDispatcher.InvokeAsync(() =>
            {
                Document doc = RequireActiveDoc();
                string payload = cmd.EndsWith('\n') ? cmd : cmd + "\n";
                doc.SendStringToExecute(payload, true, false, false);
                return (JsonNode)new JsonObject { ["sent"] = true, ["document"] = Path.GetFileName(doc.Name) };
            }).Task.ConfigureAwait(false);
        }

        if (method == "open_or_new")
            return await RunInAppContextAsync(() => HandleOpenOrNew(parms), ct).ConfigureAwait(false);

        if (method == "reload_file")
            return await RunInAppContextAsync(() => HandleReloadFile(parms), ct).ConfigureAwait(false);

        return await _uiDispatcher.InvokeAsync(() => method switch
        {
            "status" => HandleStatus(),
            "draw_entities" => HandleDrawEntities(parms),
            "audit_and_inspect" => HandleAuditAndInspect(),
            _ => throw new NotSupportedException($"Unknown method: {method}")
        }).Task.ConfigureAwait(false);
    }

    private Task<JsonNode?> RunInAppContextAsync(Func<JsonNode?> action, CancellationToken ct)
    {
        var tcs = new TaskCompletionSource<JsonNode?>(TaskCreationOptions.RunContinuationsAsynchronously);
        _uiDispatcher!.BeginInvoke(() =>
        {
            try
            {
                AcadApp.DocumentManager.ExecuteInApplicationContext(_ =>
                {
                    try { tcs.TrySetResult(action()); }
                    catch (System.Exception ex) { tcs.TrySetException(ex); }
                }, null);
            }
            catch (System.Exception ex)
            {
                tcs.TrySetException(ex);
            }
        });
        ct.Register(() => tcs.TrySetCanceled(ct));
        return tcs.Task;
    }

    private async Task<JsonNode> EvalLispAsync(string lispExpr, int timeoutMs, CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(lispExpr))
            throw new ArgumentException("LISP expression must not be empty.");

        TaskCompletionSource<string> tcs;
        lock (LispLock)
        {
            _lispTcs = new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);
            tcs = _lispTcs;
        }

        string lspPath = Path.Combine(Path.GetTempPath(), "_agy_acade_rpc.lsp");
        string lspPosix = lspPath.Replace('\\', '/');
        string wrapped =
            "(vl-load-com)\n" +
            $"(setq _agy_res (vl-catch-all-apply (function (lambda () {lispExpr}))))\n" +
            "(if (vl-catch-all-error-p _agy_res)\n" +
            "  (agy_rpc_done (strcat \"ERR|\" (vl-catch-all-error-message _agy_res)))\n" +
            "  (agy_rpc_done (strcat \"OK|\" (if (= (type _agy_res) 'STR) _agy_res (vl-princ-to-string _agy_res)))))\n" +
            "(princ)\n";
        File.WriteAllText(lspPath, wrapped, Utf8NoBom);

        await _uiDispatcher!.InvokeAsync(() =>
        {
            Document doc = RequireActiveDoc();
            string tmpDir = Path.GetTempPath().TrimEnd('\\').Replace('\\', '/');
            string trigger =
                $"\x1b\x1b(progn (if (not (vl-string-search \"{tmpDir.ToUpperInvariant()}\" (strcase (getvar \"TRUSTEDPATHS\")))) " +
                $"(setvar \"TRUSTEDPATHS\" (strcat (getvar \"TRUSTEDPATHS\") \";{tmpDir}\"))) " +
                $"(load \"{lspPosix}\"))\n";
            doc.SendStringToExecute(trigger, true, false, false);
        });

        using var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(ct);
        timeoutCts.CancelAfter(timeoutMs);
        using (timeoutCts.Token.Register(() => tcs.TrySetCanceled(timeoutCts.Token)))
        {
            string res = await tcs.Task.ConfigureAwait(false);
            if (res.StartsWith("ERR|", StringComparison.Ordinal))
                throw new InvalidOperationException("AutoCAD LISP Error: " + res[4..]);
            string value = res.StartsWith("OK|", StringComparison.Ordinal) ? res[3..] : res;
            return new JsonObject { ["value"] = value };
        }
    }

    private static Document RequireActiveDoc()
    {
        Document? doc = AcadApp.DocumentManager.MdiActiveDocument;
        if (doc == null)
            throw new InvalidOperationException("No active AutoCAD document.");
        return doc;
    }

    private static JsonObject HandleStatus()
    {
        var docs = AcadApp.DocumentManager;
        var docArr = new JsonArray();
        foreach (Document d in docs)
        {
            docArr.Add(new JsonObject
            {
                ["fullName"] = d.Name,
                ["name"] = Path.GetFileName(d.Name)
            });
        }

        Document? active = docs.MdiActiveDocument;
        JsonObject? activeObj = null;
        if (active != null)
        {
            short tmode = Convert.ToInt16(AcadApp.GetSystemVariable("TILEMODE"));
            short iunits = Convert.ToInt16(AcadApp.GetSystemVariable("INSUNITS"));
            short dbmod = Convert.ToInt16(AcadApp.GetSystemVariable("DBMOD"));
            short cmdact = Convert.ToInt16(AcadApp.GetSystemVariable("CMDACTIVE"));
            string ctab = AcadApp.GetSystemVariable("CTAB")?.ToString() ?? "";
            string fullName = active.Name;
            activeObj = new JsonObject
            {
                ["name"] = Path.GetFileName(fullName),
                ["fullName"] = fullName,
                ["activeLayout"] = ctab,
                ["activeSpace"] = tmode == 0 ? 0 : 1,
                ["tilemode"] = tmode,
                ["insunits"] = iunits,
                ["dbmod"] = dbmod,
                ["cmdactive"] = cmdact
            };
        }

        return new JsonObject
        {
            ["running"] = true,
            ["transport"] = "named-pipe-inproc-dotnet10",
            ["docCount"] = docs.Count,
            ["activeDocument"] = activeObj,
            ["documents"] = docArr
        };
    }

    private static JsonObject HandleOpenOrNew(JsonObject parms)
    {
        string path = (parms["path"]?.GetValue<string>() ?? "").Trim();
        string templateDwt = (parms["template_dwt"]?.GetValue<string>() ?? "").Trim();
        DocumentCollection dm = AcadApp.DocumentManager;
        Document targetDoc;

        if (!string.IsNullOrEmpty(path))
        {
            string fullTarget = Path.GetFullPath(path);
            Document? existing = FindDocByPath(dm, fullTarget);
            if (existing != null)
            {
                dm.MdiActiveDocument = existing;
                targetDoc = existing;
            }
            else
            {
                targetDoc = DocumentCollectionExtension.Open(dm, fullTarget, false);
                dm.MdiActiveDocument = targetDoc;
            }
            ApplyMetricStandards(targetDoc);
            return new JsonObject
            {
                ["opened"] = targetDoc.Name,
                ["activeLayout"] = SafeGetCtab(),
                ["insunits"] = 4
            };
        }
        else
        {
            if (dm.Count == 1 && dm.MdiActiveDocument != null)
            {
                try
                {
                    short titled = Convert.ToInt16(AcadApp.GetSystemVariable("DWGTITLED"));
                    short dbmod = Convert.ToInt16(AcadApp.GetSystemVariable("DBMOD"));
                    if (titled == 0 && dbmod == 0)
                    {
                        targetDoc = dm.MdiActiveDocument;
                        ApplyMetricStandards(targetDoc);
                        return new JsonObject
                        {
                            ["created"] = Path.GetFileName(targetDoc.Name),
                            ["fullName"] = targetDoc.Name,
                            ["insunits"] = 4
                        };
                    }
                }
                catch { }
            }
            string tpl = !string.IsNullOrEmpty(templateDwt) && File.Exists(templateDwt) ? templateDwt : "acadiso.dwt";
            targetDoc = DocumentCollectionExtension.Add(dm, tpl);
            dm.MdiActiveDocument = targetDoc;
            ApplyMetricStandards(targetDoc);
            return new JsonObject
            {
                ["created"] = Path.GetFileName(targetDoc.Name),
                ["fullName"] = targetDoc.Name,
                ["insunits"] = 4
            };
        }
    }

    private static string SafeGetCtab()
    {
        try { return AcadApp.GetSystemVariable("CTAB")?.ToString() ?? ""; }
        catch { return ""; }
    }

    private static JsonObject HandleReloadFile(JsonObject parms)
    {
        string targetPath = Path.GetFullPath(parms["target_path"]!.GetValue<string>());
        string? sourcePath = parms["source_path"]?.GetValue<string>();
        bool force = parms["force"]?.GetValue<bool>() ?? false;
        DocumentCollection dm = AcadApp.DocumentManager;
        string? backupPath = null;
        Document? tmpDoc = null;

        var toClose = new List<Document>();
        foreach (Document d in dm)
        {
            if (string.Equals(Path.GetFullPath(d.Name), targetPath, StringComparison.OrdinalIgnoreCase))
                toClose.Add(d);
        }

        foreach (Document d in toClose)
        {
            dm.MdiActiveDocument = d;
            short dbmod = Convert.ToInt16(AcadApp.GetSystemVariable("DBMOD"));
            if (dbmod != 0 && !force)
            {
                string ts = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                string dir = Path.Combine(Path.GetDirectoryName(targetPath)!, "_backup_unsaved");
                Directory.CreateDirectory(dir);
                backupPath = Path.Combine(dir, $"{Path.GetFileNameWithoutExtension(targetPath)}_unsaved_{ts}{Path.GetExtension(targetPath)}");
                d.Database.SaveAs(backupPath, DwgVersion.Current);
            }
            if (dm.Count <= 1)
                tmpDoc = DocumentCollectionExtension.Add(dm, "acadiso.dwt");
            DocumentExtension.CloseAndDiscard(d);
        }

        if (!string.IsNullOrWhiteSpace(sourcePath) && File.Exists(sourcePath))
            File.Move(Path.GetFullPath(sourcePath), targetPath, overwrite: true);

        Document newDoc = DocumentCollectionExtension.Open(dm, targetPath, false);
        dm.MdiActiveDocument = newDoc;
        if (tmpDoc != null)
        {
            try { DocumentExtension.CloseAndDiscard(tmpDoc); } catch { }
        }

        return new JsonObject
        {
            ["reloaded"] = newDoc.Name,
            ["activeLayout"] = SafeGetCtab(),
            ["backupCreated"] = backupPath
        };
    }

    private static Document? FindDocByPath(DocumentCollection dm, string fullPath)
    {
        foreach (Document d in dm)
        {
            if (string.Equals(Path.GetFullPath(d.Name), fullPath, StringComparison.OrdinalIgnoreCase))
                return d;
        }
        return null;
    }

    private static void ApplyMetricStandards(Document doc)
    {
        using DocumentLock _ = doc.LockDocument();
        Database db = doc.Database;
        db.Insunits = UnitsValue.Millimeters;
        db.Measurement = MeasurementValue.Metric;
        using Transaction tr = db.TransactionManager.StartTransaction();
        EnsureVnArialTextStyle(db, tr);
        tr.Commit();
    }

    private static ObjectId EnsureVnArialTextStyle(Database db, Transaction tr)
    {
        var tst = (TextStyleTable)tr.GetObject(db.TextStyleTableId, OpenMode.ForRead);
        if (tst.Has("VN_ARIAL"))
            return tst["VN_ARIAL"];

        tst.UpgradeOpen();
        var tsr = new TextStyleTableRecord
        {
            Name = "VN_ARIAL",
            Font = new Autodesk.AutoCAD.GraphicsInterface.FontDescriptor("Arial", false, false, 0, 34),
            XScale = 0.82
        };
        ObjectId id = tst.Add(tsr);
        tr.AddNewlyCreatedDBObject(tsr, true);
        return id;
    }

    private static void EnsureLayer(Database db, Transaction tr, string layerName, int? colorIndex, string? linetype)
    {
        var lt = (LayerTable)tr.GetObject(db.LayerTableId, OpenMode.ForRead);
        LayerTableRecord ltr;
        if (lt.Has(layerName))
        {
            ltr = (LayerTableRecord)tr.GetObject(lt[layerName], OpenMode.ForWrite);
        }
        else
        {
            lt.UpgradeOpen();
            ltr = new LayerTableRecord { Name = layerName };
            lt.Add(ltr);
            tr.AddNewlyCreatedDBObject(ltr, true);
        }
        if (colorIndex.HasValue)
            ltr.Color = Color.FromColorIndex(ColorMethod.ByAci, (short)colorIndex.Value);

        if (!string.IsNullOrWhiteSpace(linetype))
        {
            var ltt = (LinetypeTable)tr.GetObject(db.LinetypeTableId, OpenMode.ForRead);
            if (!ltt.Has(linetype))
            {
                try { db.LoadLineTypeFile(linetype, "acadiso.lin"); }
                catch
                {
                    try { db.LoadLineTypeFile(linetype, "acad.lin"); } catch { }
                }
            }
            if (ltt.Has(linetype))
                ltr.LinetypeObjectId = ltt[linetype];
        }
    }

    private static Point3d ReadPt3(JsonNode? node)
    {
        var arr = node!.AsArray();
        double x = arr[0]!.GetValue<double>();
        double y = arr[1]!.GetValue<double>();
        double z = arr.Count >= 3 ? arr[2]!.GetValue<double>() : 0.0;
        return new Point3d(x, y, z);
    }

    private static Point2d ReadPt2(JsonNode? node)
    {
        var arr = node!.AsArray();
        return new Point2d(arr[0]!.GetValue<double>(), arr[1]!.GetValue<double>());
    }

    private static JsonObject HandleDrawEntities(JsonObject parms)
    {
        Document doc = RequireActiveDoc();
        JsonArray entities = parms["entities"]?.AsArray() ?? new JsonArray();
        string space = parms["space"]?.GetValue<string>() ?? "ModelSpace";
        bool zoom = parms["zoom_extents"]?.GetValue<bool>() ?? true;
        bool autoSave = parms["auto_save"]?.GetValue<bool>() ?? true;

        int drawn = 0;
        Database db = doc.Database;

        using (doc.LockDocument())
        {
            // Atomic Transaction: any exception aborts & rolls back 100% of entities.
            using Transaction tr = db.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
            ObjectId spaceId = space == "PaperSpace" ? bt[BlockTableRecord.PaperSpace] : bt[BlockTableRecord.ModelSpace];
            var btr = (BlockTableRecord)tr.GetObject(spaceId, OpenMode.ForWrite);
            ObjectId vnArialId = EnsureVnArialTextStyle(db, tr);
            var seenLayers = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

            foreach (JsonNode? item in entities)
            {
                if (item is not JsonObject e) continue;
                string layer = (e["layer"]?.GetValue<string>() ?? "").Trim();
                if (!string.IsNullOrEmpty(layer) && seenLayers.Add(layer))
                {
                    int? col = e["color"]?.GetValue<int>();
                    string? ltype = e["linetype"]?.GetValue<string>();
                    EnsureLayer(db, tr, layer, col, ltype);
                }

                string etype = e["type"]?.GetValue<string>() ?? "";
                Entity? ent = etype switch
                {
                    "line" => new Line(ReadPt3(e["p1"]), ReadPt3(e["p2"])),
                    "circle" => new Circle(ReadPt3(e["center"]), Vector3d.ZAxis, e["radius"]!.GetValue<double>()),
                    "arc" => new Arc(ReadPt3(e["center"]), e["radius"]!.GetValue<double>(), e["start_angle_rad"]!.GetValue<double>(), e["end_angle_rad"]!.GetValue<double>()),
                    "lwpolyline" => CreatePolyline(e),
                    "text" => CreateText(e, vnArialId),
                    "mtext" => CreateMText(e, vnArialId),
                    "hatch" => CreateHatch(e, btr, tr),
                    "insert_block" => CreateBlockInsert(e, bt, btr, tr),
                    "mleader" => CreateMLeader(e),
                    "table" => CreateTable(e, vnArialId),
                    "dim_aligned" => CreateDimAligned(e),
                    "dim_linear" => CreateDimLinear(e),
                    "dim_diameter" => CreateDimDiameter(e),
                    _ => throw new ArgumentException($"Unsupported entity type: {etype}")
                };

                if (ent != null)
                {
                    if (!string.IsNullOrEmpty(layer))
                        ent.Layer = layer;
                    if (etype != "insert_block" && etype != "hatch")
                    {
                        btr.AppendEntity(ent);
                        tr.AddNewlyCreatedDBObject(ent, true);
                    }
                    drawn++;
                }
            }
            tr.Commit();
        }

        if (zoom)
        {
            try { AcadApp.DocumentManager.MdiActiveDocument?.SendStringToExecute("_.ZOOM _E ", true, false, false); } catch { }
        }
        doc.Editor.Regen();

        if (autoSave)
            SaveIfTitled(doc);

        return new JsonObject
        {
            ["drawn"] = drawn,
            ["document"] = Path.GetFileName(doc.Name),
            ["space"] = space,
            ["saved"] = autoSave,
            ["atomic"] = true
        };
    }

    private static void SaveIfTitled(Document doc)
    {
        short titled = Convert.ToInt16(AcadApp.GetSystemVariable("DWGTITLED"));
        if (titled == 0) return;
        string fn = doc.Name;
        if (fn.EndsWith(".dxf", StringComparison.OrdinalIgnoreCase))
            doc.Database.DxfOut(fn, 16, DwgVersion.Current);
        else
            doc.Database.SaveAs(fn, DwgVersion.Current);
    }

    private static Polyline CreatePolyline(JsonObject e)
    {
        var pts = e["points"]!.AsArray();
        var pl = new Polyline();
        for (int i = 0; i < pts.Count; i++)
            pl.AddVertexAt(i, ReadPt2(pts[i]), 0, 0, 0);
        if (e["closed"]?.GetValue<bool>() == true)
            pl.Closed = true;
        return pl;
    }

    private static DBText CreateText(JsonObject e, ObjectId vnArialId) => new()
    {
        TextString = e["text"]?.GetValue<string>() ?? "",
        Position = ReadPt3(e["insert"]),
        Height = e["height"]?.GetValue<double>() ?? 2.5,
        TextStyleId = vnArialId
    };

    private static MText CreateMText(JsonObject e, ObjectId vnArialId)
    {
        var mt = new MText
        {
            Location = ReadPt3(e["insert"]),
            Width = e["width"]?.GetValue<double>() ?? 50.0,
            Contents = e["text"]?.GetValue<string>() ?? "",
            TextStyleId = vnArialId
        };
        if (e["height"] != null)
            mt.TextHeight = e["height"]!.GetValue<double>();
        return mt;
    }

    private static Hatch CreateHatch(JsonObject e, BlockTableRecord btr, Transaction tr)
    {
        var pts = e["boundary_points"]!.AsArray();
        var loop = new Polyline();
        for (int i = 0; i < pts.Count; i++)
            loop.AddVertexAt(i, ReadPt2(pts[i]), 0, 0, 0);
        loop.Closed = true;
        btr.AppendEntity(loop);
        tr.AddNewlyCreatedDBObject(loop, true);

        var hatch = new Hatch();
        btr.AppendEntity(hatch);
        tr.AddNewlyCreatedDBObject(hatch, true);
        hatch.SetHatchPattern(HatchPatternType.PreDefined, e["pattern"]?.GetValue<string>() ?? "ANSI31");
        if (e["scale"] != null)
            hatch.PatternScale = e["scale"]!.GetValue<double>();
        hatch.Associative = true;
        hatch.AppendLoop(HatchLoopTypes.Outermost, new ObjectIdCollection { loop.ObjectId });
        hatch.EvaluateHatch(true);
        return hatch;
    }

    private static BlockReference CreateBlockInsert(JsonObject e, BlockTable bt, BlockTableRecord btr, Transaction tr)
    {
        string blockName = e["block_name"]!.GetValue<string>();
        if (!bt.Has(blockName))
            throw new ArgumentException($"Block '{blockName}' not found in drawing BlockTable.");

        ObjectId blkDefId = bt[blockName];
        var blkDef = (BlockTableRecord)tr.GetObject(blkDefId, OpenMode.ForRead);
        var br = new BlockReference(ReadPt3(e["insert"]), blkDefId)
        {
            ScaleFactors = new Scale3d(
                e["xscale"]?.GetValue<double>() ?? 1.0,
                e["yscale"]?.GetValue<double>() ?? 1.0,
                e["zscale"]?.GetValue<double>() ?? 1.0),
            Rotation = e["rotation_rad"]?.GetValue<double>() ?? 0.0
        };
        string? layer = e["layer"]?.GetValue<string>();
        if (!string.IsNullOrEmpty(layer))
            br.Layer = layer;

        btr.AppendEntity(br);
        tr.AddNewlyCreatedDBObject(br, true);

        JsonObject? attrs = e["attributes"]?.AsObject();
        foreach (ObjectId attId in blkDef)
        {
            if (tr.GetObject(attId, OpenMode.ForRead) is AttributeDefinition ad && !ad.Constant)
            {
                var ar = new AttributeReference();
                ar.SetAttributeFromBlock(ad, br.BlockTransform);
                if (attrs != null && attrs.TryGetPropertyValue(ad.Tag, out JsonNode? valNode) && valNode != null)
                    ar.TextString = valNode.ToString();
                br.AttributeCollection.AppendAttribute(ar);
                tr.AddNewlyCreatedDBObject(ar, true);
            }
        }
        return br;
    }

    private static MLeader CreateMLeader(JsonObject e)
    {
        var ml = new MLeader();
        ml.SetDatabaseDefaults();
        ml.ContentType = ContentType.MTextContent;
        var mt = new MText
        {
            Contents = e["text"]?.GetValue<string>() ?? "",
            TextHeight = e["height"]?.GetValue<double>() ?? 2.5
        };
        if (e["text_pos"] != null)
            mt.Location = ReadPt3(e["text_pos"]);
        else if (e["p2"] != null)
            mt.Location = ReadPt3(e["p2"]);
        ml.MText = mt;
        if (e["p1"] != null)
        {
            int idx = ml.AddLeaderLine(ReadPt3(e["p1"]));
            if (e["p2"] != null)
                ml.AddLastVertex(idx, ReadPt3(e["p2"]));
        }
        return ml;
    }

    private static Table CreateTable(JsonObject e, ObjectId vnArialId)
    {
        int rows = e["rows"]!.GetValue<int>();
        int cols = e["cols"]!.GetValue<int>();
        double rh = e["row_height"]?.GetValue<double>() ?? 6.0;
        double cw = e["col_width"]?.GetValue<double>() ?? 35.0;
        var tbl = new Table
        {
            Position = ReadPt3(e["insert"]),
            TableStyle = AcadApp.DocumentManager.MdiActiveDocument.Database.Tablestyle
        };
        tbl.SetSize(rows, cols);
        tbl.SetRowHeight(rh);
        tbl.SetColumnWidth(cw);
        JsonArray? data = e["data"]?.AsArray();
        if (data != null)
        {
            for (int r = 0; r < Math.Min(rows, data.Count); r++)
            {
                var rowArr = data[r]?.AsArray();
                if (rowArr == null) continue;
                for (int c = 0; c < Math.Min(cols, rowArr.Count); c++)
                {
                    tbl.Cells[r, c].TextString = rowArr[c]?.ToString() ?? "";
                    tbl.Cells[r, c].TextStyleId = vnArialId;
                }
            }
        }
        tbl.GenerateLayout();
        return tbl;
    }

    private static AlignedDimension CreateDimAligned(JsonObject e)
    {
        var d = new AlignedDimension(ReadPt3(e["p1"]), ReadPt3(e["p2"]), ReadPt3(e["text_pos"]), e["text_override"]?.GetValue<string>() ?? "", ObjectId.Null);
        return d;
    }

    private static RotatedDimension CreateDimLinear(JsonObject e)
    {
        var d = new RotatedDimension(e["angle_rad"]?.GetValue<double>() ?? 0.0, ReadPt3(e["p1"]), ReadPt3(e["p2"]), ReadPt3(e["text_pos"]), e["text_override"]?.GetValue<string>() ?? "", ObjectId.Null);
        return d;
    }

    private static DiametricDimension CreateDimDiameter(JsonObject e)
    {
        var d = new DiametricDimension(ReadPt3(e["chord1"]), ReadPt3(e["chord2"]), e["leader_len"]?.GetValue<double>() ?? 5.0, e["text_override"]?.GetValue<string>() ?? "", ObjectId.Null);
        return d;
    }

    private static JsonObject HandleAuditAndInspect()
    {
        Document doc = RequireActiveDoc();
        Database db = doc.Database;
        short activeSpace = Convert.ToInt16(AcadApp.GetSystemVariable("TILEMODE"));
        bool isPaper = activeSpace == 0;
        double pW = 0.0, pH = 0.0;

        var hardcodedDims = new JsonArray();
        var textBoxes = new List<(string Handle, string Type, double X0, double Y0, double X1, double Y1)>();
        var outOfFrame = new JsonArray();
        int total = 0;

        using (doc.LockDocument())
        using (Transaction tr = db.TransactionManager.StartTransaction())
        {
            if (isPaper)
            {
                try
                {
                    var lm = LayoutManager.Current;
                    var lo = (Layout)tr.GetObject(lm.GetLayoutId(lm.CurrentLayout), OpenMode.ForRead);
                    pW = lo.PlotPaperSize.X;
                    pH = lo.PlotPaperSize.Y;
                }
                catch { }
            }

            var bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
            ObjectId spaceId = isPaper ? bt[BlockTableRecord.PaperSpace] : bt[BlockTableRecord.ModelSpace];
            var btr = (BlockTableRecord)tr.GetObject(spaceId, OpenMode.ForRead);

            foreach (ObjectId id in btr)
            {
                if (tr.GetObject(id, OpenMode.ForRead) is not Entity ent) continue;
                total++;
                string handle = ent.Handle.ToString();
                string typeName = ent.GetType().Name;

                if (ent is Dimension dim)
                {
                    string ov = dim.DimensionText ?? "";
                    if (!string.IsNullOrEmpty(ov) && !ov.Contains("<>", StringComparison.Ordinal))
                    {
                        hardcodedDims.Add(new JsonObject
                        {
                            ["handle"] = handle,
                            ["override"] = ov,
                            ["measurement"] = Math.Round(dim.Measurement, 2)
                        });
                    }
                    double th = Math.Max(2.5, dim.Dimtxt * dim.Dimscale);
                    var tp = dim.TextPosition;
                    textBoxes.Add((handle, typeName, tp.X - 2.0 * th, tp.Y - 0.6 * th, tp.X + 2.0 * th, tp.Y + 0.6 * th));
                }
                else if (ent is DBText or MText)
                {
                    try
                    {
                        var ext = ent.GeometricExtents;
                        textBoxes.Add((handle, typeName, ext.MinPoint.X, ext.MinPoint.Y, ext.MaxPoint.X, ext.MaxPoint.Y));
                    }
                    catch { }
                }

                if (isPaper && pW > 0 && pH > 0)
                {
                    try
                    {
                        var ext = ent.GeometricExtents;
                        if (ext.MinPoint.X < -2.0 || ext.MinPoint.Y < -2.0 || ext.MaxPoint.X > pW + 2.0 || ext.MaxPoint.Y > pH + 2.0)
                        {
                            outOfFrame.Add(new JsonObject
                            {
                                ["handle"] = handle,
                                ["type"] = typeName,
                                ["maxX"] = Math.Round(ext.MaxPoint.X, 1),
                                ["maxY"] = Math.Round(ext.MaxPoint.Y, 1)
                            });
                        }
                    }
                    catch { }
                }
            }
            tr.Commit();
        }

        var overlaps = new JsonArray();
        int lim = Math.Min(textBoxes.Count, 2000);
        for (int i = 0; i < lim && overlaps.Count < 25; i++)
        {
            var a = textBoxes[i];
            for (int j = i + 1; j < lim && overlaps.Count < 25; j++)
            {
                var b = textBoxes[j];
                if (a.X0 < b.X1 && a.X1 > b.X0 && a.Y0 < b.Y1 && a.Y1 > b.Y0)
                {
                    overlaps.Add(new JsonObject
                    {
                        ["a"] = a.Handle,
                        ["b"] = b.Handle,
                        ["typeA"] = a.Type,
                        ["typeB"] = b.Type
                    });
                }
            }
        }

        return new JsonObject
        {
            ["document"] = Path.GetFileName(doc.Name),
            ["activeLayout"] = AcadApp.GetSystemVariable("CTAB")?.ToString() ?? "",
            ["totalEntities"] = total,
            ["cmdactive"] = Convert.ToInt16(AcadApp.GetSystemVariable("CMDACTIVE")),
            ["lastprompt"] = AcadApp.GetSystemVariable("LASTPROMPT")?.ToString() ?? "",
            ["hardcodedDims"] = hardcodedDims,
            ["textDimOverlaps"] = overlaps,
            ["outOfFrameEntities"] = outOfFrame
        };
    }
}
