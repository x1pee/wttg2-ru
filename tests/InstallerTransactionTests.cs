// Real filesystem fixtures only. WTTG2.exe is a text marker and is never executed.
using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

internal static class InstallerTransactionTests
{
    private static readonly string Package = AppDomain.CurrentDomain.BaseDirectory;
    // Keep fake game paths short enough for the .NET 4 installer's MAX_PATH limit.
    private static readonly string FixtureDirectory = Path.Combine(Path.GetTempPath(), "wttg2-installer-tests-" + Guid.NewGuid().ToString("N"));
    private static readonly MethodInfo Install = typeof(Program).GetMethod("InstallCore", BindingFlags.Static | BindingFlags.NonPublic);
    private static readonly MethodInfo Restore = typeof(Program).GetMethod("RestoreCore", BindingFlags.Static | BindingFlags.NonPublic);
    private static int checks;
    private static void Check(bool condition, string name)
    {
        if (!condition) throw new Exception("FAIL: " + name);
        checks++;
    }
    private static byte[] Bytes(string text) { return Encoding.UTF8.GetBytes(text); }
    private static string Sha(byte[] data)
    {
        using (var hash = SHA256.Create()) return BitConverter.ToString(hash.ComputeHash(data)).Replace("-", "").ToLowerInvariant();
    }
    private static string Fixture(bool helperExists)
    {
        string root = Path.Combine(FixtureDirectory, Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        File.WriteAllText(Path.Combine(root, "WTTG2.exe"), "fixture marker; not executable");
        if (helperExists) File.WriteAllBytes(Path.Combine(root, "helper.dat"), Bytes("existing helper"));
        File.WriteAllBytes(Path.Combine(root, "one.dat"), Bytes("English one"));
        File.WriteAllBytes(Path.Combine(root, "two.dat"), Bytes("English two"));
        Directory.CreateDirectory(Path.Combine(Package, "patches"));
        var rows = new List<string>();
        Patch(rows, "helper.dat", null, "existing helper");
        Patch(rows, "one.dat", "English one", "Russian one");
        Patch(rows, "two.dat", "English two", "Russian two");
        File.WriteAllLines(Path.Combine(Package, "manifest.tsv"), rows.ToArray(), Encoding.UTF8);
        return root;
    }
    private static void Patch(List<string> rows, string path, string original, string translated)
    {
        byte[] input = original == null ? new byte[0] : Bytes(original), output = Bytes(translated);
        string patch = path + ".gz";
        using (var file = File.Create(Path.Combine(Package, "patches", patch)))
        using (var gzip = new GZipStream(file, CompressionMode.Compress))
        using (var writer = new BinaryWriter(gzip))
        {
            writer.Write(Encoding.ASCII.GetBytes("WTTGRUP1"));
            writer.Write((long)input.Length); writer.Write((long)output.Length);
            writer.Write((byte)1); writer.Write(output.Length); writer.Write(output); writer.Write((byte)255);
        }
        rows.Add(path + "\t" + (original == null ? "-" : Sha(input)) + "\t" + Sha(output) + "\t" + patch);
    }
    private static Exception Attempt(string root, Action<string,string> copy)
    {
        try { Install.Invoke(null, new object[] { root, copy }); return null; }
        catch (TargetInvocationException error) { return error.InnerException; }
    }
    private static void NormalCopy(string source, string destination) { File.Copy(source, destination, true); }
    private static Exception AttemptRestore(string root, Action<string,string> copy)
    {
        try { Restore.Invoke(null, new object[] { root, copy }); return null; }
        catch (TargetInvocationException error) { return error.InnerException; }
    }
    private static string TranslatedFixture()
    {
        string root = Fixture(true);
        Exception error = Attempt(root, NormalCopy);
        if (error != null) throw error;
        return root;
    }
    private static int Transactions(string root)
    {
        return Directory.GetDirectories(Path.Combine(root, "WTTG2_RU_Backup"), "restore-transaction-*").Length;
    }
    private static void TranslatedStateRestored(string root)
    {
        Check(File.ReadAllText(Path.Combine(root, "one.dat")) == "Russian one", "restore rollback restores first translated file");
        Check(File.ReadAllText(Path.Combine(root, "two.dat")) == "Russian two", "restore rollback restores attempted translated file");
        Check(File.ReadAllText(Path.Combine(root, "helper.dat")) == "existing helper", "restore rollback restores deleted helper");
    }
    private static void OriginalsRestored(string root)
    {
        Check(File.ReadAllText(Path.Combine(root, "one.dat")) == "English one", "first original restored");
        Check(File.ReadAllText(Path.Combine(root, "two.dat")) == "English two", "attempted destination restored");
    }
    public static int Main(string[] args)
    {
        if (args.Length != 0)
            return (int)typeof(Program).GetMethod("Main", BindingFlags.Static | BindingFlags.NonPublic).Invoke(null, new object[] { args });
        try
        {
            string root = Fixture(true), blocked = Path.Combine(root, "two.dat");
            File.SetAttributes(blocked, FileAttributes.ReadOnly);
            try
            {
                Exception error = Attempt(root, NormalCopy);
                Check(error != null, "read-only write is rejected");
                Check(!(error is AggregateException), "unchanged read-only original does not cause false rollback failure");
                Check(File.ReadAllText(Path.Combine(root, "helper.dat")) == "existing helper", "pre-existing helper survives rollback");
                OriginalsRestored(root);
            }
            finally { File.SetAttributes(blocked, FileAttributes.Normal); }

            root = Fixture(false);
            Exception partial = Attempt(root, delegate(string source, string destination)
            {
                if (Path.GetFileName(destination) == "two.dat") { File.WriteAllText(destination, "partial write"); throw new IOException("injected partial copy"); }
                NormalCopy(source, destination);
            });
            Check(partial != null && partial.Message == "injected partial copy", "original partial-copy error retained");
            OriginalsRestored(root);
            Check(!File.Exists(Path.Combine(root, "helper.dat")), "helper created in failed attempt removed");

            root = Fixture(true);
            Exception corrupt = Attempt(root, delegate(string source, string destination)
            {
                NormalCopy(source, destination);
                if (Path.GetFileName(destination) == "two.dat") File.WriteAllText(destination, "corrupt but copy returned");
            });
            Check(corrupt != null, "final hash verification rejects corruption");
            OriginalsRestored(root);
            Check(File.ReadAllText(Path.Combine(root, "helper.dat")) == "existing helper", "verification rollback preserves existing helper");

            root = Fixture(false);
            Exception newPartial = Attempt(root, delegate(string source, string destination)
            {
                File.WriteAllText(destination, "partial new helper");
                throw new IOException("injected first-file failure");
            });
            Check(newPartial != null, "first file partial-copy failure reported");
            Check(!File.Exists(Path.Combine(root, "helper.dat")), "partially written new helper removed");
            OriginalsRestored(root);

            root = Fixture(false); blocked = Path.Combine(root, "two.dat");
            try
            {
                Exception failedRollback = Attempt(root, delegate(string source, string destination)
                {
                    NormalCopy(source, destination);
                    if (Path.GetFileName(destination) == "two.dat")
                    {
                        File.SetAttributes(destination, FileAttributes.ReadOnly);
                        throw new IOException("injected failure followed by blocked rollback");
                    }
                });
                var aggregate = failedRollback as AggregateException;
                Check(aggregate != null && aggregate.InnerExceptions.Count == 2, "original failure and rollback failure both retained");
                Check(aggregate.Message.Contains("two.dat") && aggregate.Message.Contains("injected failure"), "rollback report identifies destination and original error");
                Check(File.ReadAllText(Path.Combine(root, "one.dat")) == "English one", "rollback continues after another file cannot be restored");
                Check(!File.Exists(Path.Combine(root, "helper.dat")), "rollback continues to remove newly created helper");
            }
            finally { File.SetAttributes(blocked, FileAttributes.Normal); }

            root = Fixture(true);
            Check(Attempt(root, NormalCopy) == null, "normal installation succeeds");
            Check(File.ReadAllText(Path.Combine(root, "one.dat")) == "Russian one", "first translation installed");
            Check(File.ReadAllText(Path.Combine(root, "two.dat")) == "Russian two", "second translation installed");
            Check(File.ReadAllText(Path.Combine(root, "helper.dat")) == "existing helper", "normal install preserves existing helper");
            Check(File.ReadAllText(Path.Combine(root, "WTTG2_RU_Backup", "one.dat")) == "English one", "backup retains original");
            Check(Attempt(root, NormalCopy) == null, "already-translated install is idempotent");

            root = TranslatedFixture(); blocked = Path.Combine(root, "two.dat");
            File.SetAttributes(blocked, FileAttributes.ReadOnly);
            try
            {
                Exception restoreFailure = AttemptRestore(root, NormalCopy);
                Check(restoreFailure != null && !(restoreFailure is AggregateException), "read-only restore failure rolls back completely");
                TranslatedStateRestored(root);
                Check(Transactions(root) == 0, "complete restore rollback cleans its snapshots");
            }
            finally { File.SetAttributes(blocked, FileAttributes.Normal); }

            root = TranslatedFixture();
            Exception restorePartial = AttemptRestore(root, delegate(string source, string destination)
            {
                if (Path.GetFileName(destination) == "two.dat") { File.WriteAllText(destination, "partial restore"); throw new IOException("injected partial restore"); }
                NormalCopy(source, destination);
            });
            Check(restorePartial != null && restorePartial.Message == "injected partial restore", "partial restore failure retained: " + restorePartial);
            TranslatedStateRestored(root);
            Check(Transactions(root) == 0, "partial-write rollback cleans its snapshots");

            root = TranslatedFixture();
            Exception restoreCorrupt = AttemptRestore(root, delegate(string source, string destination)
            {
                NormalCopy(source, destination);
                if (Path.GetFileName(destination) == "two.dat") File.WriteAllText(destination, "corrupt restored bytes");
            });
            Check(restoreCorrupt != null, "restore final verification rejects corruption");
            TranslatedStateRestored(root);
            Check(Transactions(root) == 0, "verification rollback cleans its snapshots");

            root = TranslatedFixture(); blocked = Path.Combine(root, "two.dat");
            try
            {
                Exception restoreBlocked = AttemptRestore(root, delegate(string source, string destination)
                {
                    NormalCopy(source, destination);
                    if (Path.GetFileName(destination) == "two.dat") { File.SetAttributes(destination, FileAttributes.ReadOnly); throw new IOException("restore rollback blocked"); }
                });
                var aggregate = restoreBlocked as AggregateException;
                Check(aggregate != null && aggregate.InnerExceptions.Count == 2, "restore reports original and rollback errors");
                Check(aggregate.Message.Contains("two.dat") && aggregate.Message.Contains("restore-transaction-"), "restore rollback failure reports destination and retained snapshot path");
                Check(File.ReadAllText(Path.Combine(root, "one.dat")) == "Russian one", "restore rollback continues after failed destination");
                Check(File.ReadAllText(Path.Combine(root, "helper.dat")) == "existing helper", "restore rollback still recovers helper after another failure");
                Check(Transactions(root) == 1, "incomplete restore rollback retains snapshots");
                string snapshot = Directory.GetDirectories(Path.Combine(root, "WTTG2_RU_Backup"), "restore-transaction-*")[0];
                Check(File.ReadAllText(Path.Combine(snapshot, "two.dat")) == "Russian two", "retained snapshot contains exact pre-restore bytes");
            }
            finally { File.SetAttributes(blocked, FileAttributes.Normal); }

            root = TranslatedFixture();
            File.WriteAllText(Path.Combine(root, "one.dat"), "English one");
            Exception mixedFailure = AttemptRestore(root, delegate(string source, string destination)
            {
                string snapshot = Directory.GetDirectories(Path.Combine(root, "WTTG2_RU_Backup"), "restore-transaction-*")[0];
                Check(!File.Exists(Path.Combine(snapshot, "one.dat")), "already-English file is not unnecessarily snapshotted");
                File.WriteAllText(destination, "partial mixed restore"); throw new IOException("mixed-state restore failure");
            });
            Check(mixedFailure != null, "partially restored fixture failure reported");
            Check(File.ReadAllText(Path.Combine(root, "one.dat")) == "English one", "prior English file stays English during rollback");
            Check(File.ReadAllText(Path.Combine(root, "two.dat")) == "Russian two", "prior Russian file restored during mixed-state rollback");
            Check(File.ReadAllText(Path.Combine(root, "helper.dat")) == "existing helper", "mixed-state rollback restores helper");

            root = TranslatedFixture();
            File.Delete(Path.Combine(root, "one.dat"));
            Exception missingFailure = AttemptRestore(root, delegate(string source, string destination)
            {
                NormalCopy(source, destination);
                if (Path.GetFileName(destination) == "two.dat") throw new IOException("failure after recreating missing original");
            });
            Check(missingFailure != null, "restore accepts previously absent original and reports later failure");
            Check(!File.Exists(Path.Combine(root, "one.dat")), "rollback restores prior absence instead of retaining recreated original");
            Check(File.ReadAllText(Path.Combine(root, "two.dat")) == "Russian two", "missing-file fixture restores prior translated bytes");
            Check(File.ReadAllText(Path.Combine(root, "helper.dat")) == "existing helper", "missing-file fixture restores deleted helper");

            root = TranslatedFixture();
            File.WriteAllText(Path.Combine(root, "two.dat"), "independent addon modification");
            Exception modified = AttemptRestore(root, NormalCopy);
            Check(modified != null, "independent modification blocks restore before mutation");
            Check(File.ReadAllText(Path.Combine(root, "one.dat")) == "Russian one", "modification guard preserves other translated files");
            Check(File.ReadAllText(Path.Combine(root, "two.dat")) == "independent addon modification", "modification guard preserves addon bytes");
            Check(File.ReadAllText(Path.Combine(root, "helper.dat")) == "existing helper" && Transactions(root) == 0, "modification guard preserves helper and avoids transaction writes");

            root = TranslatedFixture();
            Check(AttemptRestore(root, NormalCopy) == null, "normal restore succeeds");
            OriginalsRestored(root);
            Check(!File.Exists(Path.Combine(root, "helper.dat")), "successful restore removes added helper");
            Check(Transactions(root) == 0, "successful restore cleans only its transaction snapshots");
            Check(File.ReadAllText(Path.Combine(root, "WTTG2_RU_Backup", "one.dat")) == "English one", "successful restore preserves original backup");
            Check(AttemptRestore(root, NormalCopy) == null, "already-restored operation is idempotent");
            Console.WriteLine("INSTALLER TRANSACTION PASS: " + checks + " assertions");
            return 0;
        }
        catch (Exception error) { Console.Error.WriteLine(error); return 1; }
    }
}
