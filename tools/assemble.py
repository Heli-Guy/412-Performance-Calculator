s=open('/home/claude/w/app.html').read()
W='/home/claude/w/'
t=(s.replace('/*CSS*/',open(W+'css429.css').read()).replace('/*DATA*/',open(W+'charts412.json').read())
   .replace('/*IMGS*/',open(W+'imgs412.json').read()).replace('/*IMGSA*/',open(W+'catA_img.json').read())
   .replace('/*DATAA*/',open(W+'catA.json').read()).replace('/*CATAENGINE*/',open(W+'catA_engine.js').read())
   .replace('/*CATAUI*/',open(W+'catA_ui.js').read()).replace('/*ROCUI*/',open(W+'roc_ui.js').read())
   .replace('/*IMGSR*/',open(W+'roc_img.json').read()).replace('/*DATAR*/',open(W+'roc.json').read()))
open(W+'index.html','w').write(t)
import os; print(os.path.getsize(W+'index.html')//1024,'KB')
