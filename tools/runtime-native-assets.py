"""Read-only inventory of the exact tutorial caption renderers and parents."""
import json
from pathlib import Path
import inspect_game as ig
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

original = Path(r'W:\Games\Welcome to the Game II\WTTG2_RU_Backup\WTTG2_Data')
live = Path(r'W:\Games\Welcome to the Game II\WTTG2_Data')
generator = TypeTreeGenerator('2017.3.0f3')
generator.load_local_dll_folder(str(live/'Managed'))
results = []
sources = []
for current in sorted(live.iterdir()):
    if not (current.name.endswith('.assets') or (current.name.startswith('level') and current.name[5:].isdigit())):
        continue
    source = original/current.name
    if not source.exists():
        source = current
    sources.append(source)
env = ig.UnityPy.load(*(str(source) for source in sources))
env.typetree_generator = generator
for obj in env.objects:
        if obj.type.name != 'MonoBehaviour':
            continue
        head = obj.parse_monobehaviour_head()
        try:
            script = head.m_Script.deref_parse_as_object()
        except Exception:
            continue
        if script.m_ClassName != 'TutorialTextHook':
            continue
        tree = obj.read_typetree(nodes=obj.generate_monobehaviour_node())
        result = {'file':obj.assets_file.name,'id':obj.path_id,'fields':tree,'hierarchy':[]}
        result['native_renderers'] = []
        for field in ('myText','myText2'):
            pointer = tree[field]
            if pointer['m_FileID'] != 0:
                raise AssertionError('Unexpected external caption renderer')
            renderer = obj.assets_file.objects[pointer['m_PathID']]
            renderer_object = renderer.parse_monobehaviour_head().m_GameObject.deref_parse_as_object()
            scripts = []
            for component_entry in renderer_object.m_Component:
                component = component_entry.component.deref()
                if component.type.name == 'MonoBehaviour':
                    scripts.append(component.parse_monobehaviour_head().m_Script.deref_parse_as_object().m_ClassName)
                else:
                    scripts.append(component.type.name)
            result['native_renderers'].append({'field':field,'object':renderer_object.m_Name,'components':scripts})
        game_object = head.m_GameObject.deref_parse_as_object()
        visited = set()
        for _ in range(6):
            if game_object is None or game_object.object_reader.path_id in visited:
                break
            visited.add(game_object.object_reader.path_id)
            node = {'name':game_object.m_Name,'components':[]}
            transform = None
            for entry in game_object.m_Component:
                pointer = entry.component
                reader = pointer.deref()
                info = {'class':reader.type.name,'id':reader.path_id}
                if reader.type.name in ('RectTransform','Transform'):
                    transform = reader.parse_as_object()
                elif reader.type.name == 'MonoBehaviour':
                    try:
                        info['script'] = reader.parse_monobehaviour_head().m_Script.deref_parse_as_object().m_ClassName
                    except Exception:
                        pass
                node['components'].append(info)
            result['hierarchy'].append(node)
            if transform is None or not transform.m_Father.path_id:
                break
            parent_transform = transform.m_Father.deref_parse_as_object()
            game_object = parent_transform.m_GameObject.deref_parse_as_object()
        results.append(result)
report = ig.OUT/'runtime-native-assets.json'
report.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
