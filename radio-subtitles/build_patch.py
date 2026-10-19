"""Build a narrow subtitle-table patch; never rewrite unrelated caption rows."""
import argparse, base64, hashlib, json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
UNKNOWN='[Неразборчиво по рации]'

def sha(data):return hashlib.sha256(data).hexdigest()
def name(row):return base64.b64decode(row.split(b'\t')[0],validate=True).decode('utf-8')

def build(original,review):
    records=review['clips']
    replacements={}
    for key,item in records.items():
        end=0.0; rows=[]
        for seg in item['segments']:
            start,finish=float(seg['start']),float(seg['end'])
            text=seg['ru']
            assert math.isfinite(start) and math.isfinite(finish)
            assert 0<=start<finish<=item['duration']+.001,(key,start,finish)
            assert start>=end,(key,'overlap')
            assert text and '\t' not in text and '\n' not in text and '\r' not in text
            # Square brackets distinguish uncertain audio from spoken words.
            rows.append(b'\t'.join([base64.b64encode(key.encode()),str(start).encode(),str(finish).encode(),base64.b64encode(text.encode())]))
            end=finish
        assert rows,key
        replacements[key]=rows
    newline=b'\r\n' if b'\r\n' in original else b'\n'
    original_rows=original.splitlines(keepends=True)
    seen=set();output=[];unchanged=[]
    for row in original_rows:
        if not row.strip():output.append(row);unchanged.append(row);continue
        key=name(row)
        if key.startswith('PS'):
            assert key in replacements,('unreviewed radio clip',key)
            if key not in seen:
                output.extend(r+newline for r in replacements[key]);seen.add(key)
        else:
            output.append(row);unchanged.append(row)
    assert seen==set(replacements),(seen,set(replacements))
    result=b''.join(output)
    # Compare the exact bytes of every unrelated caption, including line endings.
    result_unrelated=[row for row in result.splitlines(keepends=True) if not row.strip() or not name(row).startswith('PS')]
    assert result_unrelated==unchanged,'unrelated subtitle changed'
    stats={'before_sha256':sha(original),'after_sha256':sha(result),'radio_clips':len(seen),
           'radio_segments':sum(len(v) for v in replacements.values()),'non_radio_rows_unchanged':len(unchanged),
           'clips_with_translated_speech':sum(any(seg['ru']!=UNKNOWN for seg in v['segments']) for v in records.values()),
           'fully_unintelligible_clips':sum(all(seg['ru']==UNKNOWN for seg in v['segments']) for v in records.values())}
    return result,stats

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--review',type=Path,default=ROOT/'reviewed-radio.json')
    parser.add_argument('--output',type=Path,default=ROOT/'subtitles.tsv')
    args=parser.parse_args()
    result,stats=build(args.input.read_bytes(),json.loads(args.review.read_text('utf-8')))
    args.output.write_bytes(result)
    (ROOT/'patch-validation.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
