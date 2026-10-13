import {createRequire} from 'node:module';
import path from 'node:path';
const [root,nodeRoot]=process.argv.slice(2),require=createRequire(path.join(nodeRoot,'package.json'));
const esbuild=require('esbuild');
await esbuild.build({entryPoints:[path.join(root,'tests/ui/entry.jsx')],outfile:path.join(root,'evidence/ui-fixture-bundle.js'),bundle:true,format:'iife',platform:'browser',alias:{'@hermes/plugin-sdk':path.join(root,'tests/ui/sdk.jsx'),'react':require.resolve('react'),'react-dom/client':require.resolve('react-dom/client'),'react/jsx-runtime':require.resolve('react/jsx-runtime')},define:{'process.env.NODE_ENV':'"production"'}});
console.log('UI component bundled with explicit SDK adapter, not live Electron acceptance.');
