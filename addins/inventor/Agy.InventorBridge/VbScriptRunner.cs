using System.IO;
using System.Reflection;
using System.Runtime.Loader;
using Inventor;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.VisualBasic;
using InvFile = System.IO.File;
using InvPath = System.IO.Path;

namespace Agy.InventorBridge;

internal static class VbScriptRunner
{
    private static List<MetadataReference>? _cachedRefs;

    private static List<MetadataReference> GetMetadataReferences()
    {
        if (_cachedRefs != null)
            return _cachedRefs;

        var refs = new List<MetadataReference>();
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (Assembly asm in AppDomain.CurrentDomain.GetAssemblies())
        {
            if (asm.IsDynamic) continue;
            string loc = "";
            try { loc = asm.Location; } catch { }
            if (!string.IsNullOrEmpty(loc) && InvFile.Exists(loc) && seen.Add(loc))
            {
                try { refs.Add(MetadataReference.CreateFromFile(loc)); } catch { }
            }
        }

        string interopPath = InvPath.Combine(InventorBridgeAddIn.InventorBinDir, "Autodesk.Inventor.Interop.dll");
        if (InvFile.Exists(interopPath) && seen.Add(interopPath))
            refs.Add(MetadataReference.CreateFromFile(interopPath));

        string selfPath = typeof(InventorBridgeAddIn).Assembly.Location;
        if (!string.IsNullOrEmpty(selfPath) && InvFile.Exists(selfPath) && seen.Add(selfPath))
            refs.Add(MetadataReference.CreateFromFile(selfPath));

        string runtimeDir = System.Runtime.InteropServices.RuntimeEnvironment.GetRuntimeDirectory();
        foreach (string extraDll in new[] { "Microsoft.VisualBasic.Core.dll", "Microsoft.VisualBasic.dll" })
        {
            string p = InvPath.Combine(runtimeDir, extraDll);
            if (InvFile.Exists(p) && seen.Add(p))
                refs.Add(MetadataReference.CreateFromFile(p));
        }

        _cachedRefs = refs;
        return refs;
    }

    public static object? CompileAndRunInTransaction(Inventor.Application inv, Document doc, string script)
    {
        string vbSource =
            "Option Strict Off\r\n" +
            "Option Infer On\r\n" +
            "Imports System\r\n" +
            "Imports System.IO\r\n" +
            "Imports System.Math\r\n" +
            "Imports System.Linq\r\n" +
            "Imports System.Collections.Generic\r\n" +
            "Imports Inventor\r\n" +
            "Imports Agy.InventorBridge\r\n" +
            "Public Class __AgyScriptClass\r\n" +
            "    Public Shared Function Execute(ThisApplication As Inventor.Application, ThisDoc As AgyDocWrapper) As Object\r\n" +
            script + "\r\n" +
            "        Return Nothing\r\n" +
            "    End Function\r\n" +
            "End Class\r\n";

        SyntaxTree tree = VisualBasicSyntaxTree.ParseText(vbSource);
        var compilation = VisualBasicCompilation.Create(
            $"AgyInvDynamic_{Guid.NewGuid():N}",
            new[] { tree },
            GetMetadataReferences(),
            new VisualBasicCompilationOptions(OutputKind.DynamicallyLinkedLibrary));

        using var peStream = new MemoryStream();
        var emitResult = compilation.Emit(peStream);
        if (!emitResult.Success)
        {
            var errors = emitResult.Diagnostics
                .Where(d => d.Severity == DiagnosticSeverity.Error)
                .Select(d => d.ToString());
            throw new InvalidOperationException("VB/iLogic compile error: " + string.Join(" | ", errors));
        }

        peStream.Position = 0;
        var scriptAlc = new AssemblyLoadContext(null, isCollectible: true);
        scriptAlc.Resolving += (_, name) =>
        {
            if (string.Equals(name.Name, "Agy.InventorBridge", StringComparison.OrdinalIgnoreCase))
                return typeof(InventorBridgeAddIn).Assembly;
            string candidate = InvPath.Combine(InventorBridgeAddIn.InventorBinDir, name.Name + ".dll");
            return InvFile.Exists(candidate) ? AssemblyLoadContext.Default.LoadFromAssemblyPath(candidate) : null;
        };

        try
        {
            Assembly compiledAsm = scriptAlc.LoadFromStream(peStream);
            MethodInfo execMethod = compiledAsm.GetType("__AgyScriptClass")!.GetMethod("Execute")!;

            Transaction txn = inv.TransactionManager.StartTransaction((_Document)doc, "Agy.RunScript");
            try
            {
                object? retVal = execMethod.Invoke(null, new object[] { inv, new AgyDocWrapper(doc) });
                doc.Update2(true);
                txn.End();
                return retVal;
            }
            catch
            {
                txn.Abort(); // 100% Atomic rollback of all sketches, features, parameters, and constraints
                throw;
            }
        }
        finally
        {
            scriptAlc.Unload();
        }
    }
}
