"""fetch_subzarr.py - copy one resolution group of an open-data zarr (v2) for a z range, byte for byte.
Copies the root metadata (.zgroup, .zattrs, metadata.json) and <group>/.zarray/.zattrs, then every chunk file whose
z-chunk index overlaps [z0, z1) in that group's voxels (all y, x). Missing chunks (404) are skipped: they read back as
the fill value, exactly as in the bucket. Resumable (existing files are kept).
Usage: python fetch_subzarr.py <bucket key of the .zarr> <group> <z0> <z1> <out.zarr> [threads]"""
import concurrent.futures as cf, json, os, sys, time, urllib.error, urllib.request

B = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/"
key, grp, z0, z1, out = sys.argv[1].rstrip("/"), sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
nthr = int(sys.argv[6]) if len(sys.argv) > 6 else 32


def get(rel, required=False):
    dst = os.path.join(out, rel)
    if os.path.exists(dst):
        return "kept"
    for attempt in range(6):  # S3 occasionally resets connections under parallel load: retry with backoff
        try:
            data = urllib.request.urlopen(B + key + "/" + rel, timeout=120).read()
            break
        except urllib.error.HTTPError as e:
            if e.code in (403, 404) and not required:
                return "missing"
            if e.code < 500 or attempt == 5:
                raise
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            if attempt == 5:
                raise
        time.sleep(2 ** attempt)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst + ".part", "wb") as fh:
        fh.write(data)
    os.replace(dst + ".part", dst)
    return "got"


for rel in (".zgroup", ".zattrs", "metadata.json"):
    get(rel)
get(f"{grp}/.zarray", required=True); get(f"{grp}/.zattrs")
za = json.load(open(os.path.join(out, grp, ".zarray")))
sep = za.get("dimension_separator", ".")
(Z, Y, X), (cz, cy, cx) = za["shape"], za["chunks"]
zc = range(max(0, z0 // cz), min((Z + cz - 1) // cz, (z1 + cz - 1) // cz))


def list_keys(prefix):  # S3 ListObjectsV2: only chunks that exist (empty chunks are absent in these stores)
    import urllib.parse, xml.etree.ElementTree as ET
    ns = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}; keys = []; token = None
    while True:
        q = {"list-type": "2", "prefix": f"{key}/{prefix}", "max-keys": "1000"}
        if token: q["continuation-token"] = token
        for attempt in range(6):
            try:
                x = ET.fromstring(urllib.request.urlopen(B + "?" + urllib.parse.urlencode(q), timeout=120).read()); break
            except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
                if attempt == 5: raise
                time.sleep(2 ** attempt)
        keys += [k.find("s:Key", ns).text[len(key) + 1:] for k in x.findall("s:Contents", ns)]
        if x.findtext("s:IsTruncated", namespaces=ns) != "true": return keys
        token = x.findtext("s:NextContinuationToken", namespaces=ns)


with cf.ThreadPoolExecutor(16) as ex:
    rels = sorted(r for ks in ex.map(lambda k: list_keys(f"{grp}/{k}{sep}"), zc) for r in ks)
counts = {}
with cf.ThreadPoolExecutor(nthr) as ex:
    for r in ex.map(get, rels):
        counts[r] = counts.get(r, 0) + 1
print(f"{key} group {grp} z {z0}-{z1} (z-chunks {zc.start}-{zc.stop - 1} of {cz}): {counts}")
