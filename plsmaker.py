#!/usr/bin/python

class PLS:
	def __init__(self, filename):
		self.f=open(filename,"w")
		self.f.write("""
[HEADER]
FORMAT=IXYZRTUVWATC,Options,65,Type,17,Size-U,11,Size-V,11,Points-U,11,Points-V,11,Dir,5,Avg,5,Pos1,17,Pos2,17,Pos3,17,Link,9,File,222,Layer,65,Area,49,DoseFactor,11,Dwelltime,11,Stepsize,11,SplDwell,11,SplStep,11,CurveStep,11,CurveDwell,11,DotDwell,11,FBMSArea,11,FBMSLines,11,SplDot,5,Time,17,Timestamp,17,Method,17,Dot,16,StepsizeU,16,StepsizeV,16
WAFERLAYOUT=DEFAULT.wlo
LotID=
WaferID=
Slot=
MinimizeWin=FALSE

[COLUMNS]
No.=W:25,!VISIBLE,!SHOWDIM
ID=W:25,VISIBLE,!SHOWDIM
X=W:50,!VISIBLE,SHOWDIM
Y=W:50,!VISIBLE,SHOWDIM
Z=W:50,!VISIBLE,SHOWDIM
R=W:50,!VISIBLE,SHOWDIM
T=W:50,!VISIBLE,SHOWDIM
U=W:50,VISIBLE,SHOWDIM
V=W:50,VISIBLE,SHOWDIM
W=W:50,!VISIBLE,SHOWDIM
Attribute=W:55,VISIBLE,DEFAULT:A,!SHOWDIM
Template=W:55,VISIBLE,DEFAULT:UV,!SHOWDIM
Comment=W:203,VISIBLE,!SHOWDIM
Options=W:165,VISIBLE,!SHOWDIM
Type=W:85,VISIBLE,!SHOWDIM
Size-U=W:55,!VISIBLE,DIM:um,SHOWDIM
Size-V=W:55,!VISIBLE,DIM:um,SHOWDIM
Points-U=W:55,!VISIBLE,DIM:px,SHOWDIM
Points-V=W:55,!VISIBLE,DIM:px,SHOWDIM
Dir=W:15,!VISIBLE,!SHOWDIM
Avg=W:25,!VISIBLE,!SHOWDIM
Pos1=W:85,VISIBLE,DIM:um,SHOWDIM
Pos2=W:85,VISIBLE,DIM:um,SHOWDIM
Pos3=W:85,VISIBLE,DIM:um,SHOWDIM
Link=W:25,VISIBLE,!SHOWDIM
File=W:160,VISIBLE,!SHOWDIM
Layer=W:80,VISIBLE,!SHOWDIM
Area=W:245,!VISIBLE,!SHOWDIM
DoseFactor=W:55,VISIBLE,!SHOWDIM
Dwelltime=W:55,!VISIBLE,DIM:ms,SHOWDIM
Stepsize=W:55,!VISIBLE,DIM:um,SHOWDIM
SplDwell=W:55,!VISIBLE,DIM:ms,SHOWDIM
SplStep=W:55,!VISIBLE,DIM:um,SHOWDIM
CurveStep=W:69,!VISIBLE,DIM:um,SHOWDIM
CurveDwell=W:55,!VISIBLE,DIM:ms,SHOWDIM
DotDwell=W:55,!VISIBLE,DIM:ms,SHOWDIM
FBMSArea=W:88,VISIBLE,DIM:mm/s,SHOWDIM
FBMSLines=W:81,VISIBLE,DIM:mm/s,SHOWDIM
SplDot=W:10,!VISIBLE,!SHOWDIM
Time=W:85,VISIBLE,!SHOWDIM
Timestamp=W:85,!VISIBLE,!SHOWDIM
Method=W:85,!VISIBLE,!SHOWDIM
Dot=W:20,!VISIBLE,!SHOWDIM
StepsizeU=W:50,VISIBLE,!SHOWDIM
StepsizeV=W:50,VISIBLE,!SHOWDIM

[DATA]
""")
		self.dataLine="%(id)i,0.000000,0.000000,0.000000,0.000000,0.000000,%(u).6f,%(v).6f,0.000000,%(attrib)s,UV,%(comment)s,,EXPOSURE,%(Usize).3f,%(Vsize).3f,,,,,50.000,50.000,,,%(filename)s,%(layer)s,0.00;0.00;%(Usize).2f;%(Vsize).2f,%(dosefactor)f,,,,,,,,,,%(spldot)s,%(time)s,%(timestamp)s,%(method)s,%(dot)s,%(stepsizeU)s,%(stepsizeV)s\n"
		self.id=0
		self.x0={'attrib':'XN','filename':'','comment':'','Usize':0,'Vsize':0,'layer':'0','dosefactor':1,'stepsizeU':'','stepsizeV':'','dot':'','method':'','timestamp':'','time':'','spldot':''}
	def setDefault(self,x):
		for xx in x:
			self.x0[xx]=x[xx]
	def AddStruct(self,x,area):
		x['id']=self.id
		self.id+=1
		for k in self.x0:
			if not k in x:
				x[k]=self.x0[k]
		if x['Vsize']==0:
			x['Vsize']=area[3]/1000.0
		if x['Usize']==0:
			x['Usize']=area[2]/1000.0
		self.f.write(self.dataLine%x)
	def close(self):
		self.f.close()
