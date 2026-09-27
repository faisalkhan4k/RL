import {defineConfig} from 'vite';
export default defineConfig({base:'/ui/',build:{outDir:'../sales_agent/static/ui',emptyOutDir:true},server:{proxy:{'/api':{target:'http://127.0.0.1:8000',ws:true},'/static':'http://127.0.0.1:8000','/research':'http://127.0.0.1:8000'}}});
