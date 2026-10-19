using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;
using System.Diagnostics;

class Entry { public string path,original,translated,patch; }
class Program {
 static string Package {get{return AppDomain.CurrentDomain.BaseDirectory;}}
 static string Hash(string path) {using(var f=File.OpenRead(path))using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();}
 static string Full(string root,string relative) {
  string path=Path.GetFullPath(Path.Combine(root,relative.Replace('/',Path.DirectorySeparatorChar)));
  if(!path.StartsWith(Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))throw new Exception("Недопустимый путь в пакете.");
  return path;
 }
 static List<Entry> Entries() {
  var entries=new List<Entry>();foreach(string line in File.ReadAllLines(Path.Combine(Package,"manifest.tsv"),Encoding.UTF8)) {
   if(line.Length==0||line.StartsWith("#"))continue;string[] p=line.Split('\t');if(p.Length!=4)throw new Exception("Повреждён manifest.tsv.");
   entries.Add(new Entry{path=p[0],original=p[1],translated=p[2],patch=p[3]});
  }return entries;
 }
 static void CheckGame(string game) {
  if(!File.Exists(Path.Combine(game,"WTTG2.exe")))throw new Exception("Выберите папку с WTTG2.exe.");
  string executable=Path.GetFullPath(Path.Combine(game,"WTTG2.exe"));
  foreach(var process in Process.GetProcessesByName("WTTG2")) {
   try {
    if(String.Equals(Path.GetFullPath(process.MainModule.FileName),executable,StringComparison.OrdinalIgnoreCase))throw new Exception("Закройте игру перед установкой или восстановлением языка.");
   }catch(System.ComponentModel.Win32Exception){throw new Exception("Не удалось проверить запущенную игру. Закройте её перед установкой.");}
   catch(InvalidOperationException){}
   finally{process.Dispose();}
  }
 }
 static void ApplyPatch(string original,string patch,string output) {
  byte[] src=File.Exists(original)?File.ReadAllBytes(original):new byte[0];
  using(var file=File.OpenRead(patch))using(var gzip=new GZipStream(file,CompressionMode.Decompress))using(var reader=new BinaryReader(gzip)) {
   if(Encoding.ASCII.GetString(reader.ReadBytes(8))!="WTTGRUP1")throw new Exception("Неверный формат патча.");
   long expected=reader.ReadInt64(),target=reader.ReadInt64();if(expected!=src.LongLength)throw new Exception("Размер оригинального файла не совпадает.");
   Directory.CreateDirectory(Path.GetDirectoryName(output));using(var dest=File.Create(output)) {
    while(true) {int tag=reader.ReadByte();if(tag==255)break;
     if(tag==0){long start=reader.ReadInt64();int size=reader.ReadInt32();if(start<0||size<0||start+size>src.LongLength)throw new Exception("Повреждён блок копирования.");dest.Write(src,(int)start,size);}
     else if(tag==1){int size=reader.ReadInt32();if(size<0||size>256*1024*1024)throw new Exception("Повреждён блок вставки.");byte[] data=reader.ReadBytes(size);if(data.Length!=size)throw new Exception("Патч обрезан.");dest.Write(data,0,data.Length);}
     else throw new Exception("Неизвестный блок патча.");
    }if(dest.Length!=target)throw new Exception("Итоговый размер не совпадает.");
   }
  }
 }
 static void Install(string game) {
  game=Path.GetFullPath(game);CheckGame(game);var entries=Entries();string backup=Path.Combine(game,"WTTG2_RU_Backup");
  bool allRussian=true;foreach(var e in entries)if(!File.Exists(Full(game,e.path))||Hash(Full(game,e.path))!=e.translated)allRussian=false;
  if(allRussian){Console.WriteLine("Русский перевод уже установлен.");return;}
  foreach(var e in entries) {
   string path=Full(game,e.path);
   if(e.original=="-"){if(File.Exists(path)&&Hash(path)!=e.translated)throw new Exception("Конфликт нового файла: "+e.path);}
   else if(!File.Exists(path)||Hash(path)!=e.original)throw new Exception("Несовместимая версия или изменён файл: "+e.path+". Требуется проверенная английская версия игры. Файлы не заменены.");
   if(File.Exists(Full(backup,e.path))&&e.original!="-"&&Hash(Full(backup,e.path))!=e.original)throw new Exception("Существующий бэкап не соответствует оригиналу: "+e.path);
  }
  Directory.CreateDirectory(backup);string staging=Path.Combine(backup,"staging");Directory.CreateDirectory(staging);
  foreach(var e in entries) {
   string path=Full(game,e.path),saved=Full(backup,e.path),prepared=Full(staging,e.path);
   if(e.original!="-"&&!File.Exists(saved)){Directory.CreateDirectory(Path.GetDirectoryName(saved));File.Copy(path,saved,false);}
   ApplyPatch(e.original=="-"?Full(staging,"missing-original.tmp"):path,Full(Package,"patches/"+e.patch),prepared);
   if(Hash(prepared)!=e.translated)throw new Exception("Проверка патча не пройдена: "+e.path+". Игра не изменена.");
  }
  File.Copy(Path.Combine(Package,"manifest.tsv"),Path.Combine(backup,"manifest.tsv"),true);
  var installed=new List<Entry>();
  try {
   foreach(var e in entries){string dest=Full(game,e.path);Directory.CreateDirectory(Path.GetDirectoryName(dest));File.Copy(Full(staging,e.path),dest,true);installed.Add(e);}
  }catch {
   foreach(var e in installed){string dest=Full(game,e.path);if(e.original=="-"){if(File.Exists(dest))File.Delete(dest);}else File.Copy(Full(backup,e.path),dest,true);}throw;
  }
  foreach(var e in entries)if(Hash(Full(game,e.path))!=e.translated)throw new Exception("Проверка установки не пройдена: "+e.path);
  Console.WriteLine("Русский перевод установлен. Бэкап: "+backup);
 }
 static void Restore(string game) {
  game=Path.GetFullPath(game);CheckGame(game);string backup=Path.Combine(game,"WTTG2_RU_Backup");
  if(!File.Exists(Path.Combine(backup,"manifest.tsv")))throw new Exception("Бэкап не найден: "+backup);
  var entries=new List<Entry>();foreach(string line in File.ReadAllLines(Path.Combine(backup,"manifest.tsv"),Encoding.UTF8)) {
   if(line.Length==0||line.StartsWith("#"))continue;string[] p=line.Split('\t');entries.Add(new Entry{path=p[0],original=p[1],translated=p[2],patch=p[3]});
  }
  foreach(var e in entries) {
   string current=Full(game,e.path);if(File.Exists(current)){string h=Hash(current);if(h!=e.translated&&h!=e.original)throw new Exception("Файл изменён после установки: "+e.path+". Восстановление остановлено, чтобы сохранить изменения.");}
   if(e.original!="-"&&(!File.Exists(Full(backup,e.path))||Hash(Full(backup,e.path))!=e.original))throw new Exception("Повреждён бэкап: "+e.path);
  }
  foreach(var e in entries){string current=Full(game,e.path);if(e.original=="-"){if(File.Exists(current))File.Delete(current);}else{Directory.CreateDirectory(Path.GetDirectoryName(current));File.Copy(Full(backup,e.path),current,true);}}
  foreach(var e in entries)if(e.original!="-"&&Hash(Full(game,e.path))!=e.original)throw new Exception("Ошибка проверки восстановленного файла: "+e.path);
  Console.WriteLine("Английская версия восстановлена. Бэкап сохранён.");
 }
 static void Verify(string game) {foreach(var e in Entries())if(!File.Exists(Full(game,e.path))||Hash(Full(game,e.path))!=e.translated)throw new Exception("Не совпадает русский файл: "+e.path);Console.WriteLine("Все файлы русского перевода проверены.");}
 static ulong Key(byte[] d,int i){return BitConverter.ToUInt64(d,i);}
 static void MakeDelta(string original,string translated,string patch) {
  byte[] src=File.Exists(original)?File.ReadAllBytes(original):new byte[0],dst=File.ReadAllBytes(translated);
  var index=new Dictionary<ulong,int>();for(int i=0;i+32<src.Length;i+=32){ulong key=Key(src,i);if(!index.ContainsKey(key))index.Add(key,i);}
  using(var file=File.Create(patch))using(var gzip=new GZipStream(file,CompressionMode.Compress))using(var writer=new BinaryWriter(gzip)) {
   writer.Write(Encoding.ASCII.GetBytes("WTTGRUP1"));writer.Write(src.LongLength);writer.Write(dst.LongLength);
   int p=0,pending=0;
   while(p+32<=dst.Length){int match;bool found=index.TryGetValue(Key(dst,p),out match);
    if(found){for(int j=8;j<32;j++)if(src[match+j]!=dst[p+j]){found=false;break;}}
    if(!found){p++;continue;}
    int len=32;while(match+len<src.Length&&p+len<dst.Length&&src[match+len]==dst[p+len])len++;
    if(p>pending){writer.Write((byte)1);writer.Write(p-pending);writer.Write(dst,pending,p-pending);}
    writer.Write((byte)0);writer.Write((long)match);writer.Write(len);p+=len;pending=p;
   }
   if(pending<dst.Length){writer.Write((byte)1);writer.Write(dst.Length-pending);writer.Write(dst,pending,dst.Length-pending);}writer.Write((byte)255);
  }
  Console.WriteLine(Path.GetFileName(patch)+": "+new FileInfo(patch).Length);
 }
 [STAThread] static int Main(string[] args) {
  try {
   if(args.Length==4&&args[0]=="--packdiff"){MakeDelta(args[1],args[2],args[3]);return 0;}
   if(args.Length==2){if(args[0]=="--install")Install(args[1]);else if(args[0]=="--restore")Restore(args[1]);else if(args[0]=="--verify")Verify(args[1]);else throw new Exception("Неизвестная команда.");return 0;}
   Application.EnableVisualStyles();var form=new Form();form.Text="Welcome to the Game II — русский перевод";form.Width=630;form.Height=255;form.StartPosition=FormStartPosition.CenterScreen;form.MaximizeBox=false;
   var label=new Label{Left=18,Top=20,Width=580,Height=45,Text="Выберите папку игры, в которой находится WTTG2.exe.\nУстановка автоматически сохраняет английские файлы в WTTG2_RU_Backup."};
   var field=new TextBox{Left=18,Top=78,Width=465,Text=File.Exists(Path.Combine(Package,"WTTG2.exe"))?Package:""};
   var browse=new Button{Left=495,Top=76,Width=100,Text="Обзор..."};browse.Click+=delegate{using(var d=new FolderBrowserDialog()){d.Description="Папка с WTTG2.exe";if(d.ShowDialog()==DialogResult.OK)field.Text=d.SelectedPath;}};
   var install=new Button{Left=18,Top=126,Width=280,Height=36,Text="Установить русский"};var restore=new Button{Left=315,Top=126,Width=280,Height=36,Text="Вернуть английский"};
   EventHandler action=delegate(object sender,EventArgs ev){try{install.Enabled=restore.Enabled=false;form.UseWaitCursor=true;if(sender==install)Install(field.Text);else Restore(field.Text);MessageBox.Show(sender==install?"Русский перевод установлен. Английские файлы сохранены в WTTG2_RU_Backup.":"Английская версия восстановлена. Бэкап сохранён.","Готово",MessageBoxButtons.OK,MessageBoxIcon.Information);}catch(Exception e){MessageBox.Show(e.Message,"Установка остановлена",MessageBoxButtons.OK,MessageBoxIcon.Error);}finally{install.Enabled=restore.Enabled=true;form.UseWaitCursor=false;}};
   install.Click+=action;restore.Click+=action;form.Controls.AddRange(new Control[]{label,field,browse,install,restore});Application.Run(form);return 0;
  }catch(Exception e){Console.Error.WriteLine(e.Message);return 1;}
 }
}
