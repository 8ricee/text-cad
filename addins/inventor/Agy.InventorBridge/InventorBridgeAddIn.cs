using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Runtime.Loader;
using System.Text;
using System.Text.Json.Nodes;
using System.Windows.Forms;
using Inventor;
using InvFile = System.IO.File;
using InvPath = System.IO.Path;

namespace Agy.InventorBridge;

public sealed class AgyDocWrapper
{
    public Document Document { get; }
    public AgyDocWrapper(Document doc) => Document = doc;
}

[ComVisible(true)]
[Guid("9D4C2B7E-61F3-4A88-BC52-8E17D3A94C22")]
public sealed class InventorBridgeAddIn : ApplicationAddInServer
{
    public const string PipeName = "agy-inventor-direct";
    internal const string InventorBinDir = @"C:\Program Files\Autodesk\Inventor 2027\Bin";
    private static readonly Encoding Utf8NoBom = new UTF8Encoding(false);

    private Inventor.Application? _inv;
    private Control? _uiControl;
    private CancellationTokenSource? _cts;
    private Task? _serverTask;

    public object? Automation => null;

    public void Activate(ApplicationAddInSite addInSiteObject, bool firstTime)
    {
        try { RegisterBinResolver(); } catch { }
        _inv = addInSiteObject.Application;
        _uiControl = new Control();
        _ = _uiControl.Handle; // Bind Win32 HWND on Inventor's Main STA UI thread
        _cts = new CancellationTokenSource();
        _serverTask = Task.Run(() => RunPipeServerLoopAsync(_cts.Token));
    }

    private static void RegisterBinResolver()
    {
        var alc = AssemblyLoadContext.GetLoadContext(typeof(InventorBridgeAddIn).Assembly);
        if (alc != null)
        {
            alc.Resolving += (_, name) =>
            {
                string candidate = InvPath.Combine(InventorBinDir, name.Name + ".dll");
                return InvFile.Exists(candidate) ? AssemblyLoadContext.Default.LoadFromAssemblyPath(candidate) : null;
            };
        }
        AppDomain.CurrentDomain.AssemblyResolve += (_, args) =>
        {
            var an = new AssemblyName(args.Name);
            string candidate = InvPath.Combine(InventorBinDir, an.Name + ".dll");
            return InvFile.Exists(candidate) ? Assembly.LoadFrom(candidate) : null;
        };
    }

    public void Deactivate()
    {
        _cts?.Cancel();
        _uiControl?.Dispose();
        _uiControl = null;
        _inv = null;
    }

    public void ExecuteCommand(int commandID)
    {
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
                    JsonNode? result = InvokeOnSta(() => Dispatch(method, parms));
                    resp = new JsonObject
                    {
                        ["id"] = reqId,
                        ["ok"] = true,
                        ["result"] = result
                    };
                }
                catch (System.Exception ex)
                {
                    System.Exception root = UnwrapException(ex);
                    resp = new JsonObject
                    {
                        ["id"] = reqId,
                        ["ok"] = false,
                        ["error"] = $"{root.Message} [{root.GetType().Name}]"
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

    private static System.Exception UnwrapException(System.Exception ex)
    {
        while (ex is TargetInvocationException tie && tie.InnerException != null)
            ex = tie.InnerException;
        return ex;
    }

    private T InvokeOnSta<T>(Func<T> func)
    {
        if (_uiControl == null || _inv == null)
            throw new InvalidOperationException("Inventor STA UI bridge not initialized.");
        if (_uiControl.InvokeRequired)
            return (T)_uiControl.Invoke(func);
        return func();
    }

    private JsonNode? Dispatch(string method, JsonObject parms) => method switch
    {
        "status" => HandleStatus(),
        "create_or_open" => HandleCreateOrOpen(parms),
        "run_script" => HandleRunScript(parms),
        "check_constraints_and_interference" => HandleCheckConstraints(),
        "update_parameters" => HandleUpdateParameters(parms),
        "export_flat_pattern_dxf" => HandleExportFlatPatternDxf(parms),
        _ => throw new NotSupportedException($"Unknown method: {method}")
    };

    private JsonObject HandleStatus()
    {
        JsonObject? activeObj = null;
        if (_inv!.ActiveDocument != null)
        {
            Document d = _inv.ActiveDocument;
            activeObj = new JsonObject
            {
                ["name"] = d.DisplayName,
                ["fullName"] = d.FullFileName,
                ["type"] = (int)d.DocumentType,
                ["dirty"] = d.Dirty
            };
        }

        string activeIpj = "";
        try { activeIpj = _inv.DesignProjectManager.ActiveDesignProject?.FullFileName ?? ""; } catch { }

        return new JsonObject
        {
            ["running"] = true,
            ["transport"] = "named-pipe-inproc-dotnet10",
            ["caption"] = _inv.Caption,
            ["docCount"] = _inv.Documents.Count,
            ["activeProject"] = activeIpj,
            ["activeDocument"] = activeObj
        };
    }

    private JsonObject HandleCreateOrOpen(JsonObject parms)
    {
        string docType = parms["doc_type"]?.GetValue<string>() ?? "part_sheet_metal";
        string savePath = parms["save_path"]?.GetValue<string>() ?? "";
        string ipjPath = parms["ipj_path"]?.GetValue<string>() ?? "";
        string openPath = parms["open_path"]?.GetValue<string>() ?? "";

        if (!string.IsNullOrWhiteSpace(ipjPath))
        {
            string fullIpj = InvPath.GetFullPath(ipjPath);
            DesignProjectManager pm = _inv!.DesignProjectManager;
            DesignProject? targetProj = null;
            foreach (DesignProject dp in pm.DesignProjects)
            {
                if (string.Equals(InvPath.GetFullPath(dp.FullFileName), fullIpj, StringComparison.OrdinalIgnoreCase))
                {
                    targetProj = dp;
                    break;
                }
            }
            targetProj ??= pm.DesignProjects.AddExisting(fullIpj);
            targetProj.Activate(true);
        }

        Document d;
        if (!string.IsNullOrWhiteSpace(openPath))
        {
            d = _inv!.Documents.Open(InvPath.GetFullPath(openPath), true);
        }
        else
        {
            DocumentTypeEnum typeEnum = docType switch
            {
                "assembly" => DocumentTypeEnum.kAssemblyDocumentObject,
                "drawing" => DocumentTypeEnum.kDrawingDocumentObject,
                _ => DocumentTypeEnum.kPartDocumentObject
            };
            string tpl = docType == "part_sheet_metal"
                ? _inv!.FileManager.GetTemplateFile(
                    DocumentTypeEnum.kPartDocumentObject,
                    SystemOfMeasureEnum.kMetricSystemOfMeasure,
                    DraftingStandardEnum.kDefault_DraftingStandard,
                    "{9C464203-9BAE-11D3-8BAD-0060B0CE6BB4}")
                : _inv!.FileManager.GetTemplateFile(typeEnum, SystemOfMeasureEnum.kMetricSystemOfMeasure);

            d = _inv.Documents.Add(typeEnum, tpl, true);
            if (!string.IsNullOrWhiteSpace(savePath))
            {
                string fullSave = InvPath.GetFullPath(savePath);
                string? dir = InvPath.GetDirectoryName(fullSave);
                if (!string.IsNullOrEmpty(dir))
                    Directory.CreateDirectory(dir);
                d.SaveAs(fullSave, false);
            }
        }

        return new JsonObject
        {
            ["displayName"] = d.DisplayName,
            ["fullFileName"] = d.FullFileName,
            ["documentType"] = (int)d.DocumentType
        };
    }

    private JsonObject HandleRunScript(JsonObject parms)
    {
        string script = (parms["ilogic_script"]?.GetValue<string>()
            ?? parms["script"]?.GetValue<string>()
            ?? parms["powershell_script"]?.GetValue<string>()
            ?? "").Trim();

        if (string.IsNullOrEmpty(script))
            throw new ArgumentException("ilogic_script must not be empty.");

        if (script.Contains("$inv.", StringComparison.OrdinalIgnoreCase) || script.Contains("$doc.", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException(
                "PowerShell COM scripts ($inv / $doc) have been replaced by in-process .NET VB.NET / iLogic rules (use ThisApplication and ThisDoc.Document).");
        }

        Document doc = _inv!.ActiveDocument ?? throw new InvalidOperationException("No active Inventor document.");
        object? retVal = VbScriptRunner.CompileAndRunInTransaction(_inv, doc, script);

        var outObj = new JsonObject
        {
            ["ok"] = true,
            ["document"] = doc.DisplayName,
            ["atomic"] = true
        };
        if (retVal != null)
            outObj["result"] = retVal.ToString();
        return outObj;
    }

    private JsonObject HandleCheckConstraints()
    {
        Document d = _inv!.ActiveDocument ?? throw new InvalidOperationException("No active Inventor document.");
        var unconstrained = new JsonArray();
        var ungroundedDof = new JsonArray();
        int interferences = 0;

        if (d.DocumentType == DocumentTypeEnum.kPartDocumentObject && d is PartDocument pd)
        {
            foreach (PlanarSketch sk in pd.ComponentDefinition.Sketches)
            {
                if (sk.ConstraintStatus != ConstraintStatusEnum.kFullyConstrainedConstraintStatus)
                    unconstrained.Add(sk.Name);
            }
        }
        else if (d.DocumentType == DocumentTypeEnum.kAssemblyDocumentObject && d is AssemblyDocument ad)
        {
            ObjectCollection set1 = _inv.TransientObjects.CreateObjectCollection();
            foreach (ComponentOccurrence occ in ad.ComponentDefinition.Occurrences)
            {
                set1.Add(occ);
                if (!occ.Grounded)
                {
                    try
                    {
                        occ.GetDegreesOfFreedom(out int tDof, out ObjectsEnumerator _, out int rDof, out ObjectsEnumerator _, out Inventor.Point _);
                        if (tDof + rDof > 0)
                        {
                            ungroundedDof.Add(new JsonObject
                            {
                                ["name"] = occ.Name,
                                ["transDof"] = tDof,
                                ["rotDof"] = rDof
                            });
                        }
                    }
                    catch { }
                }
            }
            if (set1.Count >= 2)
            {
                InterferenceResults res = ad.ComponentDefinition.AnalyzeInterference(set1);
                interferences = res.Count;
            }
        }

        return new JsonObject
        {
            ["document"] = d.DisplayName,
            ["unconstrainedSketches"] = unconstrained,
            ["ungroundedDof"] = ungroundedDof,
            ["assemblyInterferences"] = interferences
        };
    }

    private JsonObject HandleUpdateParameters(JsonObject parms)
    {
        Document d = _inv!.ActiveDocument ?? throw new InvalidOperationException("No active Inventor document.");
        JsonObject updates = parms["parameters"]?.AsObject() ?? new JsonObject();

        Parameters? invParams = d switch
        {
            PartDocument pd => pd.ComponentDefinition.Parameters,
            AssemblyDocument ad => ad.ComponentDefinition.Parameters,
            DrawingDocument dd => dd.Parameters,
            _ => null
        };
        if (invParams == null)
            throw new InvalidOperationException("Active document does not expose Parameters.");

        var changed = new JsonArray();
        Transaction txn = _inv.TransactionManager.StartTransaction((_Document)d, "Agy.UpdateParameters");
        try
        {
            foreach (var kv in updates)
            {
                string name = kv.Key;
                string expr = kv.Value?.ToString() ?? "";
                Parameter? target = null;
                try { target = (Parameter)invParams.UserParameters[name]; }
                catch
                {
                    try { target = (Parameter)invParams.ModelParameters[name]; } catch { }
                }
                if (target != null)
                {
                    target.Expression = expr;
                    changed.Add(name);
                }
            }
            d.Update2(true);
            txn.End();
        }
        catch
        {
            txn.Abort();
            throw;
        }

        bool saved = false;
        if (!string.IsNullOrEmpty(d.FullFileName))
        {
            d.Save();
            saved = true;
        }

        return new JsonObject
        {
            ["document"] = d.DisplayName,
            ["updated"] = changed,
            ["saved"] = saved,
            ["atomic"] = true
        };
    }

    private JsonObject HandleExportFlatPatternDxf(JsonObject parms)
    {
        if (_inv!.ActiveDocument is not PartDocument pd)
            throw new InvalidOperationException("Active document must be an Inventor Sheet Metal Part (.ipt).");

        if (pd.ComponentDefinition is not SheetMetalComponentDefinition smcd)
            throw new InvalidOperationException("Active Part (.ipt) is not a Sheet Metal part.");

        string outPath = InvPath.GetFullPath(parms["out_path"]!.GetValue<string>());
        string? dir = InvPath.GetDirectoryName(outPath);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);

        if (!smcd.HasFlatPattern)
            smcd.Unfold();

        const string fmt =
            "FLAT PATTERN DXF?AcadVersion=2018&OuterProfileLayer=OUTER_PROFILE&InteriorProfilesLayer=INNER_CUTS" +
            "&BendUpLayer=BEND_UP&BendUpLayerLineType=37633&BendDownLayer=BEND_DOWN&BendDownLayerLineType=37634" +
            "&InvisibleLayers=IV_TANGENT;IV_TOOL_CENTER;IV_ARC_CENTERS";

        smcd.DataIO.WriteDataToFile(fmt, outPath);
        return new JsonObject { ["exported"] = outPath };
    }
}
