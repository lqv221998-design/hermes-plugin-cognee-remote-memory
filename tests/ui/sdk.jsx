import React,{useState,useEffect,useRef,forwardRef} from 'react';
export function atom(value){const listeners=new Set();return {get:()=>value,set:v=>{value=v;listeners.forEach(fn=>fn(v));},subscribe:fn=>{listeners.add(fn);return()=>listeners.delete(fn);}};}
export const host={state:{profile:atom('fixture-A'),connectionId:atom('fixture-host')},navigate:()=>{}};
export function useValue(a){const [v,set]=useState(a.get());useEffect(()=>a.subscribe(set),[a]);return v;}
export function useQuery(options){const [data,setData]=useState(),[error,setError]=useState(),[pending,setPending]=useState(true);const live=useRef(true);const refetch=async()=>{try{const d=await options.queryFn();if(live.current){setData(d);setError(null);setPending(false);}return d;}catch(e){if(live.current){setError(e);setPending(false);}throw e;}};useEffect(()=>{live.current=true;refetch().catch(()=>{});const timer=setInterval(()=>refetch().catch(()=>{}),options.refetchInterval||60000);return()=>{live.current=false;clearInterval(timer);};},[]);return {data,error,isPending:pending,refetch};}
export const Button=props=><button {...props}/>;
export const Input=forwardRef((props,ref)=><input ref={ref} {...props}/>);
export const ROUTES_AREA='routes',SIDEBAR_NAV_AREA='sidebar',PALETTE_AREA='palette';
window.fixtureSwitchProfile=()=>host.state.profile.set('fixture-B');
