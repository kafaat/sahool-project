from typing import Callable, Dict, Any, Awaitable
TOOLS: Dict[str,Callable[...,Awaitable[Dict[str,Any]]]]={}
def tool(name:str):
  def d(fn): TOOLS[name]=fn; return fn
  return d
