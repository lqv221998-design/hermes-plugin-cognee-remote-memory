import {host,useValue,useQuery,Button,Input,ROUTES_AREA,SIDEBAR_NAV_AREA,PALETTE_AREA} from '@hermes/plugin-sdk';
import {useEffect,useRef,useState} from 'react';
import {jsx,jsxs} from 'react/jsx-runtime';
const ID='cognee-remote-memory',PATH='/cognee-remote-memory',panel={border:'1px solid var(--ui-stroke-secondary)',borderRadius:8,padding:16,display:'grid',gap:12};
function Form({ctx,scope}){
 const query=useQuery({queryKey:[ID,ctx.source,scope,'connection'],queryFn:()=>ctx.rest('/connections'),retry:false,refetchInterval:5000});
 const [url,setUrl]=useState(''),[brains,setBrains]=useState([]),[write,setWrite]=useState(''),[read,setRead]=useState([]),[capture,setCapture]=useState(false),[auto,setAuto]=useState(false),[consent,setConsent]=useState(false),[replace,setReplace]=useState(false),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState(false);
 const key=useRef(null),mounted=useRef(true),hydrated=useRef(false);
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;if(key.current)key.current.value='';};},[]);
 useEffect(()=>{if(!query.data||hydrated.current)return;const s=query.data;setUrl(s.endpoint||'');setWrite(s.write_brain||'');setRead(s.read_brains||[]);setCapture(!!s.capture);setAuto(!!s.auto_recall);hydrated.current=true;},[query.data]);
 async function action(fn,success){
  if(busy)return;setBusy(true);setMessage('');setError(false);
  try{const result=await fn();if(!mounted.current)return;setMessage(success);await query.refetch();}
  catch(e){if(mounted.current){setError(true);setMessage(e?.message||'Thao tác chưa được xác minh. Kiểm tra URL, TLS, danh tính và quyền Brain.');}}
  finally{if(key.current)key.current.value='';if(mounted.current)setBusy(false);}
 }
 function connect(){void action(async()=>{
  const pending=ctx.rest('/connect',{method:'POST',body:{endpoint:url,api_key:key.current?.value||''},timeoutMs:45000});if(key.current)key.current.value='';
  const result=await pending;if(mounted.current){setBrains(result.brains||[]);setWrite('');setRead([]);setCapture(false);setAuto(false);setConsent(false);hydrated.current=false;}return result;
 },'Đã xác minh và lưu kết nối. Chưa ghi dữ liệu, chưa thay memory provider.');}
 function refresh(){void action(async()=>{const result=await ctx.rest('/brains',{timeoutMs:60000});if(mounted.current)setBrains(result.brains||[]);return result;},'Đã tải danh mục quyền hiện tại.');}
 function save(){void action(async()=>{
  const result=await ctx.rest('/selection',{method:'POST',body:{write_brain:write,read_brains:read,capture,auto_recall:auto,acknowledge_sharing:consent},timeoutMs:60000});if(mounted.current){hydrated.current=false;setConsent(false);}return result;
 },'Đã lưu lựa chọn. Quyền thật vẫn do Cognee kiểm; chưa tự tạo Brain.');}
 const pending=busy||query.isPending||!!query.error,connected=!!query.data?.configured;
 const status=query.data?.outbox||{};
 return jsxs('section',{style:{padding:24,maxWidth:960,height:'100%',overflow:'auto',display:'grid',alignContent:'start',gap:16,color:'var(--ui-text-secondary)'},children:[
  jsx('h2',{children:'Cognee Memory'}),jsx('p',{children:'Bản thử 0.1.1 trên nền Cognee chính thức · remote HTTP · '+scope}),
  jsx('p',{children:'Không cần giao diện Cognee. Mỗi máy dùng API key của tài khoản riêng; không nhập key Admin.'}),
  query.error?jsx('div',{role:'alert',style:panel,children:'Backend plugin chưa sẵn sàng. Cần cài/bật Python plugin và khởi động backend Hermes lúc rảnh; không chỉ bật UI.'}):null,
  jsxs('fieldset',{disabled:pending,style:panel,children:[jsx('legend',{children:'1. Kết nối máy chủ'}),
   jsxs('label',{children:['Địa chỉ Cognee',jsx(Input,{'aria-label':'Địa chỉ Cognee',style:{width:'100%',boxSizing:'border-box'},value:url,onChange:e=>setUrl(e.target.value),placeholder:'https://cognee.ten-mien-noi-bo:8443 hoặc loopback cho thử local'})]}),
   jsx('p',{children:'Chỉ nhập origin, không thêm /api/v1. LAN cần HTTPS có chứng chỉ được tin cậy; không tắt kiểm TLS.'}),
   jsxs('label',{children:['API key',jsx(Input,{'aria-label':'API key',style:{width:'100%',boxSizing:'border-box'},type:'password',ref:key,autoComplete:'off',spellCheck:false,placeholder:query.data?.has_api_key?'Đã có key; để trống chỉ khi giữ đúng URL':'Nhập issued API key của người dùng thường'})]}),
   jsx('p',{children:'Key không lưu trong browser hay trả lại qua API. Hermes lưu .env của profile với quyền OS; không phải vault mã hóa.'}),
   jsx(Button,{type:'button',onClick:connect,children:busy?'Đang kiểm tra…':'Kiểm tra và lưu kết nối'}),
   connected?jsx('div',{children:'Identity: '+query.data.expected_user_id+' · Tenant: '+(query.data.expected_tenant_id||'cá nhân')}):null]}),
  jsxs('fieldset',{disabled:pending||!connected,style:panel,children:[jsx('legend',{children:'2. Chọn Brain'}),jsx(Button,{type:'button',onClick:refresh,children:'Tải lại danh mục Brain'}),
   jsx('label',{htmlFor:'write-brain',children:'Brain lưu hội thoại'}),jsx('select',{id:'write-brain','aria-label':'Brain lưu hội thoại',value:write,onChange:e=>{setWrite(e.target.value);setConsent(false);},children:[jsx('option',{value:'',children:'Chưa chọn — không tự tạo Brain'}),...brains.map(b=>jsx('option',{value:b.id,disabled:b.protected||!['read','write'].every(p=>b.permissions.includes(p)),children:b.name+' · '+b.id},b.id))]}),
   jsx('p',{children:'Người có read trên Brain này có thể đọc hội thoại đã lưu. Tên user/session không tạo riêng tư. Brain riêng phải được Admin cấp trước.'}),jsx('strong',{children:'Các Brain tra cứu'}),
   ...brains.map(b=>jsxs('label',{style:{display:'flex',gap:8},children:[jsx('input',{type:'checkbox','aria-label':'Tra cứu '+b.name,checked:read.includes(b.id),disabled:!b.permissions.includes('read'),onChange:e=>setRead(old=>e.target.checked?[...old,b.id]:old.filter(x=>x!==b.id))}),b.name+' · '+b.permissions.join(' + '),jsx('small',{children:b.id})]},b.id)),
   jsxs('label',{children:[jsx('input',{type:'checkbox',checked:capture,onChange:e=>setCapture(e.target.checked),'aria-label':'Tự lưu hội thoại mới'}),' Tự lưu hội thoại mới (user/assistant text; không system/tool/file bytes)']}),
   jsxs('label',{children:[jsx('input',{type:'checkbox',checked:auto,onChange:e=>setAuto(e.target.checked),'aria-label':'Tra cứu trước mỗi câu hỏi'}),' Tra cứu trước mỗi câu hỏi']}),
   jsxs('label',{children:[jsx('input',{type:'checkbox',checked:consent,onChange:e=>setConsent(e.target.checked),'aria-label':'Đồng ý phạm vi lưu và chia sẻ'}),' Tôi đồng ý đích lưu, phạm vi chia sẻ và LLM/embedding egress của server; không backfill lịch sử.']}),
   jsx('p',{children:'Recall: HYBRID_COMPLETION · context-only · UUID scope. Chat không được nâng thành chuẩn công ty/pháp luật.'}),jsx(Button,{type:'button',onClick:save,children:'Lưu lựa chọn Brain'})]}),
  jsxs('fieldset',{disabled:pending||!connected,style:panel,children:[jsx('legend',{children:'3. Bật bộ nhớ trên profile này'}),jsx('p',{children:'Provider đang cấu hình: '+(query.data?.provider||'built-in')}),
   jsxs('label',{children:[jsx('input',{type:'checkbox',checked:replace,onChange:e=>setReplace(e.target.checked),'aria-label':'Đồng ý thay memory provider'}),' Tôi đồng ý thay external memory provider của profile này bằng Cognee. Không áp dụng cho Default trên máy khác.']}),
   jsx(Button,{type:'button',disabled:!replace,onClick:()=>void action(()=>ctx.rest('/activate',{method:'POST',body:{acknowledge_replace:replace},timeoutMs:60000}),'Đã lưu provider. Mở phiên Hermes mới/khởi động lại lúc rảnh; chưa nghiệm thu activation live.'),children:'Bật Cognee Memory'})]}),
  jsxs('section',{style:panel,children:[jsx('h3',{children:'Trạng thái giao nhận'}),jsx('p',{children:'Queued '+(status.queued||0)+' · Sending '+(status.sending||0)+' · Raw verified '+(status.raw_verified||0)+' · Indexed '+(status.indexed||0)+' · Uncertain '+(status.uncertain||0)}),
   jsx('p',{children:'Indexed = server báo terminal completed + raw khớp; không phải nghiệm thu ngữ nghĩa/vectors. Uncertain không gửi lại mù. Outbox: '+(status.payload_storage||'')}),
   jsx(Button,{type:'button',disabled:pending||!connected,onClick:()=>void action(()=>ctx.rest('/flush',{method:'POST',body:{},timeoutMs:1260000}),'Đã xử lý một lượt hàng đợi; đối chiếu trạng thái bên trên.'),children:'Gửi lượt đang chờ'}),
   jsx(Button,{type:'button',disabled:pending||!connected,onClick:()=>void action(()=>ctx.rest('/reconcile',{method:'POST',body:{},timeoutMs:120000}),'Đã đối chiếu raw; không tự resend hoặc chạy lại indexing.'),children:'Đối chiếu uncertain (chỉ đọc)'}),
   jsx(Button,{type:'button',disabled:pending||!connected,onClick:()=>void action(async()=>{const result=await ctx.rest('/disconnect',{method:'POST',body:{}});if(mounted.current){setBrains([]);setWrite('');setRead([]);setCapture(false);setAuto(false);hydrated.current=false;}return result;},'Đã ngắt binding cục bộ, giữ outbox; không thu hồi key trên server.'),children:'Ngắt kết nối'})]}),
  message?jsx('div',{role:error?'alert':'status',style:panel,children:message}):null]});
}
export function Page({ctx}){const profile=useValue(host.state.profile),connection=useValue(host.state.connectionId||host.state.profile);const scope=String(connection||'local')+' / '+String(profile||'default');return jsx(Form,{ctx,scope},scope);}
export default {id:ID,name:'Cognee Memory',defaultEnabled:false,register(ctx){
 ctx.register({id:'memory-page',area:ROUTES_AREA,data:{path:PATH},render:()=>jsx(Page,{ctx})});
 ctx.register({id:'memory-nav',area:SIDEBAR_NAV_AREA,data:{path:PATH,label:'Cognee Memory',codicon:'plug'}});
 ctx.register({id:'memory-open',area:PALETTE_AREA,data:{id:ID+'.open',label:'Mở Cognee Memory',run:()=>host.navigate(PATH)}});

}};
