#!/usr/bin/env python3
"""Read-only Kleinanzeigen MCP server over stdio.
No ranking is performed; callers receive neutral listing and route data.
"""
import json, math, os, re, subprocess, sys
from kleinanzeigen_api import KleinanzeigenAPI

MAPS = os.environ.get("KLEINANZEIGEN_MAPS_CLIENT", "")
AMTZELL = (47.704, 9.828)  # used only when explicitly requested by the caller


def haversine_km(lat1, lon1, lat2, lon2):
 r = 6371.0
 p1, p2 = math.radians(lat1), math.radians(lat2)
 dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
 a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
 return round(2 * r * math.asin(math.sqrt(a)))


def straight_distance(ad, origin):
 if not origin or ad.latitude is None or ad.longitude is None:
  return None
 try:
  return haversine_km(float(origin["latitude"]), float(origin["longitude"]), float(ad.latitude), float(ad.longitude))
 except (KeyError, TypeError, ValueError):
  return None


def compact_listing(a, *, origin=None, include_distance=False, max_description_chars=1200, max_images=5):
 d = listing_dict(a)
 d["description"] = (d.get("description") or "")[:max(0, int(max_description_chars))]
 d["images"] = (d.get("images") or [])[:max(0, int(max_images))]
 if include_distance:
  d["distance_km"] = straight_distance(a, origin)
 return d



def listing_dict(a):
 return {"id":a.id,"title":a.title,"price":a.price,"url":a.url,"city":a.city,"zip_code":a.zip_code,"latitude":a.latitude,"longitude":a.longitude,"posted":str(a.posted) if a.posted else None,"attributes":a.attributes,"description":getattr(a,"description",None),"images":getattr(a,"images",None)}
api = KleinanzeigenAPI()
TOOLS = [
 {"name":"search_listings","description":"Search public Kleinanzeigen listings; neutral data, optional compact fields and distances. No ranking.","inputSchema":{"type":"object","properties":{"query":{"type":"string"},"category":{"type":"string"},"location":{"type":"string"},"radius_km":{"type":"number"},"min_price":{"type":"number"},"max_price":{"type":"number"},"sort":{"type":"string"},"pages":{"type":"integer"},"limit":{"type":"integer"},"exclude":{"type":"array","items":{"type":"string"}},"compact":{"type":"boolean"},"max_description_chars":{"type":"integer"},"max_images":{"type":"integer"},"include_distance":{"type":"boolean"},"origin_latitude":{"type":"number"},"origin_longitude":{"type":"number"}},"required":["query"]}},
 {"name":"get_listing","description":"Fetch one public listing by URL or Kleinanzeigen ID.","inputSchema":{"type":"object","properties":{"url":{"type":"string"},"id":{"type":"string"}}}},
 {"name":"check_availability","description":"Check a public listing and report available, reserved, deleted, or unclear.","inputSchema":{"type":"object","properties":{"url":{"type":"string"},"id":{"type":"string"}}}},
 {"name":"calculate_route","description":"Calculate driving route from an origin to a listing location or destination.","inputSchema":{"type":"object","properties":{"origin":{"type":"string"},"destination":{"type":"string"},"mode":{"type":"string","enum":["driving","cycling","walking"]}},"required":["origin","destination"]}}
]

def listing_dict(a):
 return {"id":a.id,"title":a.title,"price":a.price,"url":a.url,"city":a.city,"zip_code":a.zip_code,"latitude":a.latitude,"longitude":a.longitude,"posted":str(a.posted) if a.posted else None,"attributes":a.attributes,"description":getattr(a,"description",None),"images":getattr(a,"images",None)}

def search(args):
 q=args["query"]; limit=max(1,min(int(args.get("limit",50)),100)); pages=max(1,min(int(args.get("pages",1)),5)); kwargs={"q":q,"category":args.get("category"),"distance_km":args.get("radius_km"),"min_price":args.get("min_price"),"max_price":args.get("max_price"),"pages":pages,"size":limit}
 compact=bool(args.get("compact",False)); include_distance=bool(args.get("include_distance",False)); origin=None
 if include_distance and args.get("origin_latitude") is not None and args.get("origin_longitude") is not None:
  origin={"latitude":args["origin_latitude"],"longitude":args["origin_longitude"]}
 if args.get("location"): kwargs["location"]=args["location"]
 if args.get("sort"): kwargs["sort_type"]={"new":"DATE_DESCENDING","price_asc":"PRICE_ASCENDING","price_desc":"PRICE_DESCENDING"}.get(args["sort"],args["sort"])
 ads={}
 for a in api.search(**{k:v for k,v in kwargs.items() if v is not None}):
  text=(a.title+" "+str(getattr(a,"description",None))).lower()
  if any(x.lower() in text for x in args.get("exclude",[])): continue
  ads[a.id]=a
 rows=list(ads.values())[:limit]
 if compact:
  rows=[compact_listing(a, origin=origin, include_distance=include_distance, max_description_chars=args.get("max_description_chars",1200), max_images=args.get("max_images",5)) for a in rows]
 else:
  rows=[listing_dict(a) for a in rows]
 return {"query":q,"count":len(ads),"listings":rows}

def get_ad(args):
 ident=args.get("id")
 if not ident:
  matches=re.findall(r"(?:^|[-/])(\d{8,})(?:[-/]|$)", args.get("url",""))
  ident=matches[0] if matches else ""
 if not ident.isdigit(): raise ValueError("url or numeric id required")
 return listing_dict(api.get_ad(ident))

def availability(args):
 a=get_ad(args); text=json.dumps(a,ensure_ascii=False).lower()
 if any(x in text for x in ["gelöscht","deleted"]): status="deleted"
 elif any(x in text for x in ["reserviert","reserved"]): status="reserved"
 elif a.get("title") and a.get("url"): status="available"
 else: status="unclear"
 return {"status":status,"listing":a}

def route(args):
 if not MAPS:
  raise RuntimeError("route calculation requires KLEINANZEIGEN_MAPS_CLIENT")
 p=subprocess.run(["python3",MAPS,"distance",args["origin"],"--to",args["destination"],"--mode",args.get("mode","driving")],capture_output=True,text=True,timeout=45)
 if p.returncode: raise RuntimeError(p.stderr.strip() or "routing failed")
 return json.loads(p.stdout)

def call(name,args):
 return {"search_listings":search,"get_listing":get_ad,"check_availability":availability,"calculate_route":route}[name](args)

def main():
 for line in sys.stdin:
  try:
   req=json.loads(line); method=req.get("method"); rid=req.get("id")
   if method=="initialize": result={"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"kleinanzeigen","version":"0.1.0"}}
   elif method=="notifications/initialized": continue
   elif method=="tools/list": result={"tools":TOOLS}
   elif method=="tools/call":
    data=call(req["params"]["name"],req["params"].get("arguments",{})); result={"structuredContent":data,"content":[{"type":"text","text":json.dumps(data,ensure_ascii=False)}]}
   else:
    if rid is None: continue
    raise ValueError("method not found")
   if rid is not None: print(json.dumps({"jsonrpc":"2.0","id":rid,"result":result},ensure_ascii=False),flush=True)
  except Exception as e:
   if req.get("id") is not None: print(json.dumps({"jsonrpc":"2.0","id":req["id"],"error":{"code":-32000,"message":str(e)}},ensure_ascii=False),flush=True)
if __name__=="__main__": main()
