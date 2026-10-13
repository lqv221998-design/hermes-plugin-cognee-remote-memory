import React from 'react';
import {createRoot} from 'react-dom/client';
import plugin from '../../desktop/plugin.js';
const contributions=[];
const ctx={source:'fixture',register:c=>{contributions.push(c);return()=>{};},rest:async(path,options={})=>{const result=await fetch('/api/plugins/cognee-remote-memory'+path,{method:options.method||'GET',headers:{'Content-Type':'application/json'},body:options.body===undefined?undefined:JSON.stringify(options.body)});const value=await result.json();if(!result.ok)throw new Error(value.detail||'Fixture request rejected');return value;}};
plugin.register(ctx);
const page=contributions.find(c=>c.area==='routes');
if(!page)throw new Error('Connection route missing after plugin registration.');
createRoot(document.getElementById('root')).render(page.render());
