using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Video;
using UnityEngine.UI;
using TMPro;
using System.Text.RegularExpressions;
using System.Reflection;

namespace WTTG2RU {
 public static class Localizer {
  static Dictionary<string,string> texts;
  static Type chatType;
  static bool inputTypeChecked;static Type tmpInputType;static PropertyInfo tmpInputText;
  public static string TranslateUI(Component owner,string value) {
   if(owner!=null&&owner.GetComponentInParent<Subtitles>()!=null)return value;
   if(chatType==null)chatType=Type.GetType("DeadOrNotChatObject, Assembly-CSharp");
   if(!inputTypeChecked){inputTypeChecked=true;tmpInputType=Type.GetType("TMPro.TMP_InputField, TextMeshPro-2017.3-1.0.56-Runtime");if(tmpInputType!=null)tmpInputText=tmpInputType.GetProperty("textComponent");}
   if(owner!=null)for(Transform current=owner.transform;current!=null;current=current.parent) {
    if(chatType!=null&&current.GetComponent(chatType)!=null)return value;
    InputField input=current.GetComponent<InputField>();
    if(input!=null&&input.textComponent==owner)return value;
    if(tmpInputType!=null&&tmpInputText!=null) {
     Component tmpInput=current.GetComponent(tmpInputType);
     if(tmpInput!=null&&tmpInputText.GetValue(tmpInput,null) as Component==owner)return value;
    }
   }
   return Translate(value);
  }
  public static void ConfigureNativeCaption(Component hook,float duration) {
   Boot();Subtitles.RegisterNative(hook);
  }
  public static void RegisterTutorialAudio(Component hook,AudioClip clip) {
   Boot();Subtitles.RegisterNativeAudio(hook,clip);
  }
  public static void AudioStarted(AudioSource source) {
   Boot();Subtitles.AddAudio(source);
  }
  public static void VideoStarted(VideoPlayer player) {
   Boot();Subtitles.AddVideo(player);
  }
  public static string Translate(string value) {
   if (String.IsNullOrEmpty(value)) return value;
   try {
    if(texts==null) {
     texts=new Dictionary<string,string>();
     string file=Path.Combine(Application.dataPath,"RU/strings.tsv");
     if(File.Exists(file)) foreach(string line in File.ReadAllLines(file,Encoding.UTF8)) {
      string[] p=line.Split('\t');if(p.Length!=2)continue;
      texts[Encoding.UTF8.GetString(Convert.FromBase64String(p[0]))]=Encoding.UTF8.GetString(Convert.FromBase64String(p[1]));
     }
    }
    string key=value.Trim(),translated;
    Match networkPrompt=Regex.Match(key,@"^The WiFi network (.+) requires a\s+(.+) password\.$");
    if(networkPrompt.Success)return "Для подключения к сети «"+networkPrompt.Groups[1].Value+"» нужен пароль "+networkPrompt.Groups[2].Value+".";
    foreach(string prefix in new string[]{"Pro Tip: ","Совет: "})if(key.StartsWith(prefix,StringComparison.Ordinal))
     return "Совет: "+Translate(key.Substring(prefix.Length));
    if(Regex.IsMatch(key,@"^\d{3,5}x\d{3,5}$"))return key.Replace("x"," × ");
    if(texts.TryGetValue(key,out translated))return value.Substring(0,value.Length-value.TrimStart().Length)+translated+value.Substring(value.TrimEnd().Length);
    string[,] prefixes={{"Stock: ","В наличии: "},{"FLOOR ","ЭТАЖ "},{">  FLOOR ",">  ЭТАЖ "},{"VPN Level ","VPN, уровень "},{"GAINED: ","ПОЛУЧЕНО: "},{"LOST: ","ПОТЕРЯНО: "},{"NOTES: ","ЗАМЕТКИ: "}};
    for(int i=0;i<prefixes.GetLength(0);i++)if(key.StartsWith(prefixes[i,0],StringComparison.Ordinal))return prefixes[i,1]+key.Substring(prefixes[i,0].Length);
   }catch(Exception e){Debug.LogWarning("[WTTG2RU] Translation error: "+e.Message);}
   return value;
  }
  public static void Boot() {
   if(Subtitles.Exists)return;
   foreach(Subtitles existing in Resources.FindObjectsOfTypeAll<Subtitles>())
    if(existing!=null&&existing.gameObject.activeInHierarchy&&existing.enabled){existing.ClaimInstance();return;}
   GameObject go=new GameObject("WTTG2RU Subtitles");UnityEngine.Object.DontDestroyOnLoad(go);go.AddComponent<Subtitles>();
   Debug.Log("[WTTG2RU] Russian text and subtitles loaded.");
  }
 }
 public class Caption {public double start,end;public string text;}
 [DefaultExecutionOrder(32000)]
 public class Subtitles : MonoBehaviour {
  static Subtitles instance;
  public static bool Exists {get{return instance!=null&&instance.enabled;}}
  public void ClaimInstance(){if(instance==null)instance=this;}
  class NativeCaption {
   public Component hook;public Text primary,secondary;public AudioClip clip;
   bool suppressed,primaryEnabled,secondaryEnabled;
   public void Suppress(bool hide) {
    if(hide&&!suppressed){primaryEnabled=primary!=null&&primary.enabled;secondaryEnabled=secondary!=null&&secondary.enabled;}
    if(hide){if(primary!=null)primary.enabled=false;if(secondary!=null)secondary.enabled=false;}
    else if(suppressed){if(primary!=null)primary.enabled=primaryEnabled;if(secondary!=null)secondary.enabled=secondaryEnabled;}
    suppressed=hide;
   }
  }
  readonly Dictionary<int,NativeCaption> nativeCaptions=new Dictionary<int,NativeCaption>();
  static Text NativeText(Component hook,string name) {
   FieldInfo field=hook.GetType().GetField(name,BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public);
   return field==null?null:field.GetValue(hook) as Text;
  }
  static NativeCaption Native(Component hook) {
   if(instance==null||hook==null)return null;
   int id=hook.GetInstanceID();NativeCaption state;
   if(!instance.nativeCaptions.TryGetValue(id,out state)){state=new NativeCaption();state.hook=hook;instance.nativeCaptions[id]=state;}
   state.primary=NativeText(hook,"myText");state.secondary=NativeText(hook,"myText2");return state;
  }
  public static void RegisterNative(Component hook) {Native(hook);}
  public static void RegisterNativeAudio(Component hook,AudioClip clip) {NativeCaption state=Native(hook);if(state!=null)state.clip=clip;}
  public static void AddAudio(AudioSource source) {if(instance!=null&&source!=null&&!instance.audio.Contains(source))instance.audio.Add(source);}
  public static void AddVideo(VideoPlayer player) {if(instance!=null&&player!=null&&!instance.video.Contains(player))instance.video.Add(player);}
  void RefreshSources() {
   foreach(AudioSource source in Resources.FindObjectsOfTypeAll<AudioSource>())AddAudio(source);
   foreach(VideoPlayer player in Resources.FindObjectsOfTypeAll<VideoPlayer>())AddVideo(player);
   audio.RemoveAll(delegate(AudioSource source){return source==null;});
   video.RemoveAll(delegate(VideoPlayer player){return player==null;});
  }
  bool NativeClipIsCovered(NativeCaption state) {
   if(state.clip==null||!captions.ContainsKey(state.clip.name))return false;
   foreach(AudioSource source in audio)if(source!=null&&source.gameObject.activeInHierarchy&&source.isPlaying&&source.clip==state.clip)return true;
   return false;
  }
  void ApplyNativeCaptionVisibility(string overlay) {
   List<int> expired=new List<int>();
   bool coveredVideo=false;
   foreach(VideoPlayer player in video)if(player!=null&&player.gameObject.activeInHierarchy&&player.isPlaying&&player.clip!=null&&captions.ContainsKey(player.clip.name)){coveredVideo=true;break;}
   foreach(KeyValuePair<int,NativeCaption> entry in nativeCaptions) {
    NativeCaption state=entry.Value;
    if(state.hook==null){state.Suppress(false);expired.Add(entry.Key);continue;}
    // Tutorial narration is also kept on screen while a video plays. Hide
    // this exact native pair before canvas rendering, including both shadow
    // layers, whenever our single overlay is visible. Keep unknown clips
    // and skipped narration readable in the original panel.
    state.Suppress(!String.IsNullOrEmpty(overlay)||coveredVideo||NativeClipIsCovered(state));
   }
   foreach(int id in expired)nativeCaptions.Remove(id);
  }
  Dictionary<string,List<Caption>> captions=new Dictionary<string,List<Caption>>();
  readonly List<AudioSource> audio=new List<AudioSource>();readonly List<VideoPlayer> video=new List<VideoPlayer>();
  float refresh;string shown="";Font font;bool captureRequested,done,menuShown,optionsQA,captionQA,regressionChecked,longCaptured;string testPath;float captureTime;
  Text label;GameObject panel;RectTransform captionRect;TextGenerator measure=new TextGenerator();
  string laidOut="";int lastWidth,lastHeight;
  void Awake() {
   if(instance!=null&&instance!=this){enabled=false;gameObject.SetActive(false);Destroy(gameObject);return;}
   instance=this;
   foreach(Font candidate in Resources.FindObjectsOfTypeAll<Font>()) {
    foreach(string name in candidate.fontNames)if(name=="Cascadia Code"){font=candidate;break;}
    if(font!=null)break;
   }
   if(font==null)font=Font.CreateDynamicFontFromOSFont("Cascadia Code",24);
   string file=Path.Combine(Application.dataPath,"RU/subtitles.tsv");
   if(File.Exists(file)) foreach(string line in File.ReadAllLines(file,Encoding.UTF8))try {
    string[] p=line.Split('\t');if(p.Length!=4)continue;
    string name=Encoding.UTF8.GetString(Convert.FromBase64String(p[0]));
    Caption c=new Caption();c.start=Double.Parse(p[1],System.Globalization.CultureInfo.InvariantCulture);c.end=Double.Parse(p[2],System.Globalization.CultureInfo.InvariantCulture);c.text=Encoding.UTF8.GetString(Convert.FromBase64String(p[3]));
    if(c.start<0||c.end<=c.start||String.IsNullOrEmpty(c.text))continue;
    List<Caption> list;if(!captions.TryGetValue(name,out list)){list=new List<Caption>();captions[name]=list;}list.Add(c);
   }catch(Exception e){Debug.LogWarning("[WTTG2RU] Invalid subtitle row: "+e.Message);}
   foreach(List<Caption> list in captions.Values)list.Sort(delegate(Caption first,Caption second){return first.start.CompareTo(second.start);});
   string[] args=Environment.GetCommandLineArgs();
   for(int i=0;i+1<args.Length;i++)if(args[i]=="--ru-qa"){testPath=args[i+1];captureRequested=true;captureTime=Time.realtimeSinceStartup+45;}
   foreach(string arg in args)if(arg=="--ru-options")optionsQA=true;
   foreach(string arg in args)if(arg=="--ru-caption-qa")captionQA=true;
   if(captureRequested)Application.runInBackground=true;
   GameObject canvasObject=new GameObject("RU Caption Canvas",typeof(RectTransform));canvasObject.transform.SetParent(transform,false);
   Canvas canvas=canvasObject.AddComponent<Canvas>();canvas.renderMode=RenderMode.ScreenSpaceOverlay;canvas.sortingOrder=32767;
   panel=new GameObject("Caption",typeof(RectTransform));panel.transform.SetParent(canvasObject.transform,false);
   Image background=panel.AddComponent<Image>();background.color=new Color(0,0,0,.86f);background.raycastTarget=false;
   captionRect=panel.GetComponent<RectTransform>();captionRect.anchorMin=captionRect.anchorMax=new Vector2(.5f,0);captionRect.pivot=new Vector2(.5f,0);
   GameObject textObject=new GameObject("Text",typeof(RectTransform));textObject.transform.SetParent(panel.transform,false);
   RectTransform tr=textObject.GetComponent<RectTransform>();tr.anchorMin=Vector2.zero;tr.anchorMax=Vector2.one;tr.offsetMin=new Vector2(18,9);tr.offsetMax=new Vector2(-18,-9);
   label=textObject.AddComponent<Text>();label.font=font;label.color=Color.white;label.alignment=TextAnchor.MiddleCenter;label.raycastTarget=false;label.supportRichText=false;label.resizeTextForBestFit=false;label.horizontalOverflow=HorizontalWrapMode.Wrap;label.verticalOverflow=VerticalWrapMode.Overflow;panel.SetActive(false);
   Debug.Log("[WTTG2RU] Subtitle clips: "+captions.Count);
  }
  void OnLevelWasLoaded(int level){refresh=0;}
  void OnDestroy(){if(instance!=this)return;foreach(NativeCaption state in nativeCaptions.Values)state.Suppress(false);instance=null;}
  string GetCaption(string name,double position) {
   List<Caption> list;if(!captions.TryGetValue(name,out list))return "";
   foreach(Caption c in list)if(position>=c.start&&position<c.end)return c.text;
   return "";
  }
  void LayoutCaption(string value) {
   if(value==laidOut&&lastWidth==Screen.width&&lastHeight==Screen.height)return;
   laidOut=value;lastWidth=Screen.width;lastHeight=Screen.height;
   label.text=value;
   int size=Mathf.Clamp(Mathf.RoundToInt(Screen.height/48f),18,34);
   float width=0,height=0;
   while(true) {
    label.fontSize=size;
    TextGenerationSettings settings=label.GetGenerationSettings(Vector2.zero);
    settings.horizontalOverflow=HorizontalWrapMode.Overflow;settings.verticalOverflow=VerticalWrapMode.Overflow;
    width=Mathf.Min(Mathf.Max(40,measure.GetPreferredWidth(value,settings)),Mathf.Min(Screen.width*.88f-36,size*44f));
    settings.generationExtents=new Vector2(width,0);settings.horizontalOverflow=HorizontalWrapMode.Wrap;
    height=Mathf.Max(size*1.2f,measure.GetPreferredHeight(value,settings));
    if(height<=Screen.height*.35f||size<=16)break;
    size--;
   }
   captionRect.sizeDelta=new Vector2(Mathf.Ceil(width+36),Mathf.Ceil(height+18));
   captionRect.anchoredPosition=new Vector2(0,Mathf.Max(16,Screen.height*.025f));
  }
  readonly List<UnityEngine.Object> qaFixtures=new List<UnityEngine.Object>();
  GameObject QAFixture(string name,params Type[] components){GameObject go=new GameObject(name,components);qaFixtures.Add(go);return go;}
  void CheckRegression() {
   try {
   Localizer.Boot();Localizer.Boot();
   GameObject duplicate=QAFixture("RU Regression Duplicate");duplicate.AddComponent<Subtitles>();
   int live=0;foreach(Subtitles subtitles in Resources.FindObjectsOfTypeAll<Subtitles>())if(subtitles!=null&&subtitles.enabled&&subtitles.gameObject.activeInHierarchy)live++;
   if(live!=1)throw new Exception("More than one subtitle owner survived duplicate Boot/Awake");
   Debug.Log("[WTTG2RU] REGRESSION PASS: duplicate Boot/Awake leaves one live subtitle canvas");
   Type tutorialType=Type.GetType("TutorialTextHook, Assembly-CSharp");
   GameObject root=QAFixture("RU Regression Native",typeof(RectTransform));
   root.AddComponent<Text>();
   Component hook=root.AddComponent(tutorialType);
   Text first=QAFixture("Native primary",typeof(RectTransform)).AddComponent<Text>();
   Text second=QAFixture("Native secondary",typeof(RectTransform)).AddComponent<Text>();
   second.enabled=false;
   tutorialType.GetField("myText",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(hook,first);
   tutorialType.GetField("myText2",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(hook,second);
   string clipName="";foreach(string name in captions.Keys){clipName=name;break;}
   GameObject soundObject=QAFixture("RU Regression Audio");AudioSource sound=soundObject.AddComponent<AudioSource>();
   sound.clip=AudioClip.Create(clipName,160000,1,16000,false);qaFixtures.Add(sound.clip);sound.volume=0;sound.Play();
   Localizer.AudioStarted(sound);Localizer.RegisterTutorialAudio(hook,sound.clip);
   tutorialType.GetMethod("Process").Invoke(hook,new object[]{"OPTIONS",10f});
   if((string)tutorialType.GetField("currentText",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(hook)!=Localizer.Translate("OPTIONS"))throw new Exception("Typewriter stored English instead of complete Russian text");
   Debug.Log("[WTTG2RU] REGRESSION PASS: full native phrase translated before typewriter starts");
   ApplyNativeCaptionVisibility("");
   if(first.enabled||second.enabled)throw new Exception("Native tutorial transcript was not hidden");
   Debug.Log("[WTTG2RU] REGRESSION PASS: exact covered clip hides both native layers during subtitle gaps");
   sound.Stop();ApplyNativeCaptionVisibility("");
   if(!first.enabled||second.enabled)throw new Exception("Native renderer states were not restored after audio ended");
   Debug.Log("[WTTG2RU] REGRESSION PASS: stopped or skipped narration restores original renderer states");
   AudioClip unknown=AudioClip.Create("RU Regression Unknown",160000,1,16000,false);
   qaFixtures.Add(unknown);
   AudioClip covered=sound.clip;sound.clip=unknown;sound.Play();Localizer.RegisterTutorialAudio(hook,unknown);
   tutorialType.GetMethod("Process").Invoke(hook,new object[]{"Проверка резервного текста",10f});ApplyNativeCaptionVisibility("");
   if(!first.enabled||second.enabled)throw new Exception("Uncovered clip of same duration lost its native text");
   Debug.Log("[WTTG2RU] REGRESSION PASS: unknown clip with equal duration retains native fallback");
   ApplyNativeCaptionVisibility("Проверка реплики видео");
   if(first.enabled||second.enabled)throw new Exception("Video overlay left previous native narration visible");
   ApplyNativeCaptionVisibility("");
   if(!first.enabled||second.enabled)throw new Exception("Video overlay removal did not restore native fallback");
   Debug.Log("[WTTG2RU] REGRESSION PASS: video overlay hides persistent native pair and restores fallback");
   Type chat=Type.GetType("DeadOrNotChatObject, Assembly-CSharp");
   GameObject chatRoot=QAFixture("RU Regression Chat",typeof(RectTransform));chatRoot.AddComponent(chat);
   Text message=QAFixture("Chat message",typeof(RectTransform)).AddComponent<Text>();message.transform.SetParent(chatRoot.transform,false);message.text="NEW GAME";
   if(message.text!="NEW GAME")throw new Exception("Chat message was translated");
   Text ordinary=QAFixture("Ordinary message",typeof(RectTransform)).AddComponent<Text>();ordinary.text="NEW GAME";
   if(ordinary.text!="НОВАЯ ИГРА")throw new Exception("Ordinary text did not reach translation hook");
   Debug.Log("[WTTG2RU] REGRESSION PASS: chat stays English while ordinary UI still translates");
   GameObject inputRoot=QAFixture("RU Regression Input",typeof(RectTransform));InputField input=inputRoot.AddComponent<InputField>();
   Text inputText=QAFixture("Input contents",typeof(RectTransform)).AddComponent<Text>();inputText.transform.SetParent(inputRoot.transform,false);inputText.font=font;input.textComponent=inputText;
   Text placeholder=QAFixture("Placeholder",typeof(RectTransform)).AddComponent<Text>();placeholder.transform.SetParent(inputRoot.transform,false);placeholder.text="OPTIONS";input.placeholder=placeholder;
   input.text="NEW GAME";
   if(input.text!="NEW GAME"||inputText.text!="NEW GAME")throw new Exception("Editable input mismatch: model="+input.text+" renderer="+inputText.text);
   if(placeholder.text!=Localizer.Translate("OPTIONS"))throw new Exception("Input placeholder did not translate");
   Debug.Log("[WTTG2RU] REGRESSION PASS: editable input stays exact while placeholder translates");
   string tip=Localizer.Translate("Совет: Place your motion sensors where it makes the most sense.");
   if(!tip.StartsWith("Совет: ",StringComparison.Ordinal)||tip.IndexOf("Place your",StringComparison.Ordinal)>=0)throw new Exception("Compound loading tip was not translated");
   Debug.Log("[WTTG2RU] REGRESSION PASS: complete compound loading tip translated");
   if(Localizer.Translate("The WiFi network TestSSID requires a  WEP password.")!="Для подключения к сети «TestSSID» нужен пароль WEP.")throw new Exception("Network prompt lost name or security type");
   Debug.Log("[WTTG2RU] REGRESSION PASS: network password prompt preserves SSID and security type");
   }finally {
    foreach(UnityEngine.Object fixture in qaFixtures) {
     GameObject go=fixture as GameObject;
     if(go!=null){foreach(MonoBehaviour behaviour in go.GetComponents<MonoBehaviour>())behaviour.StopAllCoroutines();foreach(AudioSource source in go.GetComponents<AudioSource>())source.Stop();go.SetActive(false);}
     if(fixture!=null)Destroy(fixture);
    }
    qaFixtures.Clear();ApplyNativeCaptionVisibility("");
   }
  }
  void LateUpdate() {
   if(Time.realtimeSinceStartup>refresh){RefreshSources();refresh=Time.realtimeSinceStartup+.5f;}
   shown="";
   foreach(VideoPlayer p in video)if(p!=null&&p.gameObject.activeInHierarchy&&p.isPlaying&&p.clip!=null){string c=GetCaption(p.clip.name,p.time);if(c.Length>0){shown=c;break;}}
   if(shown.Length==0)foreach(AudioSource s in audio)if(s!=null&&s.gameObject.activeInHierarchy&&s.isPlaying&&s.clip!=null){string c=GetCaption(s.clip.name,s.time);if(c.Length>0){shown=c;break;}}
   if(captureRequested){
    shown=optionsQA?"":"Проверка русского языка: Ёё, Йй, Щщ, ъыьэюя.\n"+Localizer.Translate("NEW GAME")+" · "+Localizer.Translate("OPTIONS")+" · "+Localizer.Translate("CONTINUE");
    if(captionQA) {
     shown=done?"Этот сайт только что появился, и в закрытых каналах уже только о нём и говорят. Время от времени в эфире появляется новая девушка и просит о помощи. Похоже, похитители перенаправляют трансляцию сюда.":"На сайте есть какое-то голосование.";
     if(!regressionChecked&&Time.realtimeSinceStartup>captureTime-5){regressionChecked=true;try{CheckRegression();}catch(Exception e){Debug.LogError("[WTTG2RU] REGRESSION FAILED: "+e.Message);}}
    }
    if(!menuShown&&Time.realtimeSinceStartup>captureTime-8){
     Type t=Type.GetType("TitleMainMenuHook, Assembly-CSharp");
     if(t!=null)foreach(UnityEngine.Object obj in Resources.FindObjectsOfTypeAll(t)){t.GetMethod("Present").Invoke(obj,null);menuShown=true;}
     if(optionsQA){Type manager=Type.GetType("TitleManager, Assembly-CSharp");foreach(UnityEngine.Object obj in Resources.FindObjectsOfTypeAll(manager))manager.GetMethod("PresentOptions").Invoke(obj,null);}
    }
   }
   ApplyNativeCaptionVisibility(shown);
   if(label!=null){if(shown.Length>0)LayoutCaption(shown);panel.SetActive(shown.Length>0);}
   if(captureRequested&&!done&&Time.realtimeSinceStartup>captureTime){
    foreach(TMP_Text text in Resources.FindObjectsOfTypeAll<TMP_Text>())if(text.gameObject.activeInHierarchy){text.ForceMeshUpdate();Debug.Log("[WTTG2RU] UI: "+text.text+" | preferred="+text.preferredWidth+" rect="+text.rectTransform.rect.width+" fontsize="+text.fontSize+" lines="+text.textInfo.lineCount);}
    ScreenCapture.CaptureScreenshot(testPath);Debug.Log("[WTTG2RU] QA capture: "+testPath);done=true;
    if(captionQA)Debug.Log("[WTTG2RU] Caption SHORT: "+captionRect.sizeDelta+" font="+label.fontSize+" text="+shown);
   }
   if(captionQA&&done&&!longCaptured&&Time.realtimeSinceStartup>captureTime+4){ScreenCapture.CaptureScreenshot(testPath.Replace(".png","-long.png"));Debug.Log("[WTTG2RU] Caption LONG: "+captionRect.sizeDelta+" font="+label.fontSize+" text="+shown);longCaptured=true;}
   if(done&&Time.realtimeSinceStartup>captureTime+(captionQA?8:4))Application.Quit();
  }
 }
}
