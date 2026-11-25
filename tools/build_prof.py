import sys,json; sys.path.insert(0,'/home/claude/w'); from catA import *
MD='/mnt/user-data/uploads/c87318f5-BHT-412-MD-5_-_4_-_Expanded_Performance.pdf'
R={'prof_A':(F625,26,(30,150,560,560)),'prof_B':(F625,64,(25,228,560,500)),'prof_C':(F625,100,(30,255,540,548)),'prof_D':(F625,138,(25,228,560,500)),'bk411':(MD,61,(55,240,585,590))}
OUT={};IM={}
for k,(f,p,c) in R.items():
    IM[k]=image_of(getpage(f,p),pymupdf.Rect(*c),sc=2.2); OUT[k]=[c[0],c[1],c[2]-c[0],c[3]-c[1]]
json.dump(OUT,open('prof.json','w')); json.dump(IM,open('prof_img.json','w'))
print({k:len(v)//1024 for k,v in IM.items()})
