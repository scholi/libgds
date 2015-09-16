#!/usr/bin/env python
# *-* coding: utf-8 *-*

# SVN FILE: $Id: gds.py 298 2013-10-02 07:44:25Z scholi $
#
# Project Name : GDSII library
#
# Author: $Author: scholi $
# Copyright: $Copyright$
# Version: $Revision: 298 $
# Last Revision: $Date: 2013-10-02 09:44:25 +0200 (Wed, 02 Oct 2013) $
# Modified by: $LastChangedBy: scholi $
# Last Modified: $LastChangedDate: 2013-10-02 09:44:25 +0200 (Wed, 02 Oct 2013) $

import struct
import sys
import binascii
import math
import os

def MatrVectMul(A,v):
	if A==[[1,0],[0,1]]:
		return v
	return [A[0][0]*v[0]+A[0][1]*v[1],A[1][0]*v[0]+A[1][1]*v[1]]

def MatrMatrMul(A,B):
	return [
		[A[0][0]*B[0][0]+A[0][1]*B[1][0],
		A[0][0]*B[0][1]+A[0][1]*B[1][1]],
		[A[1][0]*B[0][0]+A[1][1]*B[1][0],
		A[1][0]*B[0][1]+A[1][1]*B[1][1]]]


def float2gds(x):
	if type(x)==float:
		x=struct.pack('>d',x)
	s=struct.unpack('>Q',x)[0]
	sgn = (s&0x8000000000000000)
	exp = (s&0x7ff0000000000000) >> 52
	man = (s&0x000fffffffffffff)
	man =man|0x0010000000000000
	ee=(exp-1023)
	e=65+(ee>>2)
	m=man<<ee%4
	f=(sgn) | (e<<56) | m
	r=struct.pack('>Q',f)
	return r

def gds2float(x):
	s=struct.unpack('>Q',x)[0]
	sgn=(s&0x8000000000000000)
	exp=(s&0x7f00000000000000) >> 56
	man=(s&0x00ffffffffffffff)
	e=1023+((exp-64)<<2)
	if ((man&0x00e0000000000000) >> 53) == 0:
		man = (man&0x000fffffffffffff)
		e-=4
	elif ((man&0x00c0000000000000) >> 54) == 0:
		man = (man&0x001fffffffffffff) >> 1
		e-=3
	elif ((man&0x0080000000000000) >> 55) == 0:
		man = (man&0x003fffffffffffff) >> 2
		e-=2
	else:
		man = (man&0x007fffffffffffff) >> 3
		e-=1
	f=(sgn)|(e<<52)|man
	r=struct.unpack('>d',struct.pack('>Q',f))[0]
	return r

class GDSII:
	def __init__(self,DirectWrite=False):
		self.Type2={ '\x00': (0,''),
			"\x01": (2,'H'),
			"\x02": (2,'H'),
			"\x03": (4,'i'),
			"\x05": (8,'Q'),
			"\x06": (-1,'s')}
		self.Type={
			"\x00\x02":"HEADER",
			"\x01\x02":"BGNLIB",
			"\x02\x06":"LIBNAME",
			"\x03\x05":"UNITS",
			"\x04\x00":"ENDLIB",
			"\x05\x02":"BGNSTR",
			"\x06\x06":"STRNAME",
			"\x07\x00":"ENDSTR",
			"\x08\x00":"BOUNDARY",
			"\x09\x00":"PATH",
			"\x0A\x00":"SREF",
			"\x0B\x00":"AREF",
			"\x0C\x00":"TEXT",
			"\x0D\x02":"LAYER",
			"\x0E\x02":"DATATYPE",
			"\x0F\x03":"WIDTH",
			"\x10\x03":"XY",
			"\x12\x06":"SNAME",
			"\x13\x02":"COLROW",
			"\x15\x00":"NODE",
			"\x16\x02":"TEXTTYPE",
			"\x17\x01":"PRESENTATION",
			"\x19\x06":"ASCII STRING",
			"\x1a\x01":"STRANS",
			"\x1b\x05":"MAG",
			"\x1c\x05":"ANGLE",
			"\x1f\x06":"REFLIBS",
			"\x20\x06":"FONTS",
			"\x21\x02":"PATHTYPE",
			"\x22\x02":"GENERATIONS",
			"\x23\x06":"ATTRTABLE",
			"\x26\x01":"ELFLAGS",
			"\x2a\x02":"NODETYPE",
			"\x2d\x00":"BOX",
			"\x2e\x02":"BOXTYPE",
			"\x2f\x03":"PLEX",
			"\x36\x02":"FORMAT",
			"\x37\x06":"MASK",
			"\x38\x00":"ENDMASKS",
			"\x58\x00":"FBMS"}
		self.IType=dict((k,v) for v,k in self.Type.items())
		self.structs=[]
		self.minimax=[[0,0],[0,0]]
		self.objs=[]
		self.M=[[1,0],[0,1]]
		self.shift=[0,0]
		self.loops=1
		self.macro=[]
		self.enabledMacro=False
		self.currentStructure=None
		self.area={}
		self.StrPos={}
		if DirectWrite:
			self.f=open(DirectWrite,"wb")
		else:
			self.f=None
	def writeLoop(self, loop):
		self.addObj('\x63\x06','\xaa'+'\x00'*7+struct.pack("<I",int(loop)))
	def writeDirMode(self, mode):
		if mode in ['//','par','paral','parallel']:
			mode=0
		elif mode in ['angle','ang']:
			mode=1
		elif mode in ['long','longitudinal']:
			mode=2
		elif mode in ['trans','transversal']:
			mode=3
		if type(mode)==type(1):
			if mode>=0 and mode <4:
				self.addObj('\x63\x06','\xd2'+'\x00'*7+struct.pack("<I",int(mode)))

	def writeAngleDir(self, adir):
		if adir<0:
			adir=360+adir
		if adir>=0 and adir<360:
				self.addObj('\x63\x06','\xd4'+'\x00'*5+'\x01\x00'+struct.pack("<d",adir))

	def writeFillMode(self, mode):
		if mode in [ "dir","directional"]:
			mode=0
		elif mode in [ "conc","concentric"]:
			mode=1
		elif mode in [ "rast","raster" ]:
			mode=2
		if type(mode)==type(1):
			if mode>=0 and mode <3:
				self.addObj('\x63\x06','\x9b'+'\x00'*7+struct.pack("<I",int(mode)))
	def addPoint(self, pos, layer=0, dose=1):
		self.addLine([pos[0],pos[1],pos[0],pos[1]],layer=layer,width=0,dose=dose)
	def addMarker(self, pos, size=10000, width=1000, dose=1, loop=None):
		# pos is the position of the LL corner of the marker
		# The marker is a cross (+) fitting in a (size x size) square.
		# The arms have a width of width
		a=(width-size)/2
		b=(width-size)/2
		self.addPoly([
			pos[0]+a,pos[1],
			pos[0]+b,pos[1],
			pos[0]+b,pos[1]+a,
			pos[0]+size,pos[1]+a,
			pos[0]+size,pos[1]+b,
			pos[0]+b,pos[1]+b,
			pos[0]+b,pos[1]+size,
			pos[0]+a,pos[1]+size,
			pos[0]+a,pos[1]+b,
			pos[0],pos[1]+b,
			pos[0],pos[1]+a,
			pos[0]+a,pos[1]+a],dose=dose,loop=loop)
	def addSRef(self,struct, pos=(0,0), mag=1, angle=0):
		self.addObj('SREF')
		self.addObj('SNAME',struct)
		if mag!=1:
			self.addObj('MAG',float(mag))
		if angle!=0:
			self.addObj('ANGLE',float(angle))
			A=[[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]
		self.addObj('XY',list(pos))
		self.addObj('\x11\x00')
	def addFBMS(self, pos, dose=1, width=0, layer=0, curvature=[], head=(0,0,0,0)):
		self.addObj('FBMS')
		self.addObj('LAYER',layer)
		self.addObj('DATATYPE',self.doseEnc(dose))
		if width>0:
			self.addObj('WIDTH',width)
		p=list(head)
		if curvature==[]:
			curvature=[0]*(1+len(pos)/2)
		for i in range(len(pos)/2):
			if i==0:
				p+=[0]
			elif curvature[i]>0:
				p+=[2]
			else:
				p+=[1]
			p+=pos[2*i:(2*i+2)]
			p+=[curvature[i]]
		self.addObj('XY',p)	
		self.addObj('\x11\x00')
			
	def addARef(self, struct, pos=(0,0), mag=1, angle=0, array=(1,1),spacing=(5000,5000)):
		self.addObj('AREF')
		self.addObj('SNAME',struct)
		lr=[pos[0]+array[0]*spacing[0],pos[1]]
		tl=[pos[0],pos[1]+array[1]*spacing[1]]
		if mag!=1:
			self.addObj('MAG',float(mag))
		if angle!=0:
			self.addObj('ANGLE',float(angle))
			A=[[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]
			lr=MatrVectMul(A,lr)
			tl=MatrVectMul(A,tl)
		self.addObj('COLROW',array)
		self.addObj('XY',list(pos)+lr+tl)
		self.addObj('\x11\x00')
	def uvSetShift(self,x=None,y=None):
		if x==None: x=self.shift[0]
		if y==None: y=self.shift[1]
		self.shift=[x,y]
	def uvResetM(self):
		self.M=[[1,0],[0,1]]
	def uvShift(self,x=0,y=0):
		self.shift=[self.shift[0]+x,self.shift[1]+y]
	def uvScale(self,x=1,y=1):
		self.M=MatrMatrMul([[x,0],[0,y]],self.M)
	def uvRotate(self, alpha=0):
		alpha*=math.pi/180
		self.M=MatrMatrMul([[math.cos(alpha),math.sin(alpha)],[-math.sin(alpha),math.cos(alpha)]],self.M)
	def uvMirror(self, x=False, y=False):
		self.M=MatrMatrMul([[ [1,-1][x],0],[0, [1,-1][y]]],self.M)
	def getType(self, t):
		if t in self.Type.values():
			for x in self.Type:
				if t==self.Type[x]:
					#print("%s"%(binascii.hexlify(x.encode('utf-8'))))
					return x
		else: return t

	def uv2xy(self,v):
		if self.M!=[[1,0],[0,1]]:
			v=MatrVectMul(self.M,v)
		return [self.shift[0]+v[0],self.shift[1]+v[1]]

	def encodeObj(self,t,p=[]):
		# This function is private and is only used my addObj
		# The user shouln't take care of this function
		# The hacker should know that this function converts the object of type t with arguments p to the GDS binary format
		# The type t, can be either a keyword defined my self.Type, or directly a 2-bytes binary
		if p==None: p=[]
		tt=self.getType(t)

		if tt in self.Type:
			t=self.Type[tt]
		else:
			t='UNKNOWKN'
		fmt=self.Type2[tt[1]]
		if fmt[1]=='':
			return struct.pack(">H2s",4,tt)
		if fmt[0]==-1:
			if type(p)==list or type(p)==tuple: p=p[0]
			if p[-1]!='\x00' and len(p)%2==1: p+='\x00'
			return struct.pack(">H2s%is"%(len(p)),4+len(p),tt,p)
		else:
			if type(p)!=tuple and type(p)!=list: p=[p]
			s=struct.pack(">H2s",4+len(p)*fmt[0],tt)
			for x in p:
				if fmt[1]=='Q':
					s+=float2gds(x)
				else:
					s+=struct.pack(">"+fmt[1],x)
			return s
	def doseEnc(self, dose):
		if dose<=30:
			return int(dose*1000)
		else:
			return 30000+int((dose-30)*2)

	def open(self, path):
		self.objs=[]
		bs=os.path.getsize(path)
		f=open(path,"rb")
		bLENGTH=f.read(2)
		cs=[0,0]
		lp=0
		lo=None
		while bLENGTH!='':
			v=f.tell()*100/bs
			if v>lp:
				print("%i%% done"%(v))
				lp=v
			LENGTH=struct.unpack(">H",bLENGTH)[0]
			TYPE=f.read(2)
			PARAMS=f.read(LENGTH-4)
			bLENGTH=f.read(2)
			fmt=self.Type2[TYPE[1]]
			if fmt[0]==-1:
				TXT=struct.unpack(str(LENGTH-4)+fmt[1],PARAMS)
			elif fmt[0]>0:
				if fmt[1]=='Q':
					TXT=[]
					for k in range((LENGTH-4)/8):
						TXT.append(gds2float(PARAMS[k*8:k*8+8]))
				else:
					TXT=struct.unpack(">%i%s"%((LENGTH-4)/fmt[0], fmt[1]),PARAMS)
			else:
				TXT=None
			if TYPE in self.Type:
				if self.Type[TYPE] == 'BGNSTR':
					cs[0]=len(self.objs)
				elif self.Type[TYPE] == 'ENDSTR':
					cs[1]=len(self.objs)
					self.structs.append(cs)
			if TYPE in self.Type: TYPE=self.Type[TYPE]
			else: TYPE="??? (%s)"%(binascii.hexlify(TYPE))
#			if self.f==None:
#				ob={'TYPE':TYPE,'PARAMS':TXT}
#				self.objs.append(ob)
#			else:
#				if TYPE in ['BOUNDARY','PATH','SREF','AREF','TEXT','NODE','BOX']:
#					self.f.write("[%s]\n"%(TYPE))
#				else:
#					self.f.write("\t[%s]\t%s\n"%(TYPE,TXT))
#				if TYPE in self.Type: TYPE=self.Type[TYPE]
#				else: TYPE="??? (%s)"%(binascii.hexlify(TYPE))
			if TYPE=='STRNAME':
				t=TXT[0]
				if t[-1]=='\x00': t=t[:-1]
				ff=open(path+"_"+t+".svg","w")
				ff.write("<svg xmlns=\"http://www.w3.org/2000/svg\">\n")
				ff.write("<g transform=\"scale(1,-1)\">\n")
			elif TYPE=='ENDSTR':
				ff.write("</g>\n</svg>")
				ff.close()
			if TYPE in ['BOUNDARY','PATH','SREF','AREF','TEXT','NODE','BOX']:
				lo=TYPE
			elif TYPE=='SNAME':
				los=TXT[0]
				if los[-1]=='\x00': los=los[:-1]
			elif TYPE=='XY':
				if lo in ['BOUNDARY','PATH']:
					ff.write("<path d=\"M %i,%i L"%(TXT[0],TXT[1]))
					for x in zip(TXT[2::2],TXT[3::2]):
						ff.write(" %i,%i"%x)
					if lo=='PATH':
						ff.write("\" fill=\"none\" stroke=\"black")
					ff.write("\" />\n")
				if lo in ['SREF','AREF']:
					ff.write("<g transform=\"scale(1,-1)\"><text x=\"%i\" y=\"%i\" font-size=\"10000\">%s</text></g>\n"%(TXT[0],TXT[1],los))
	def show(self,a=0,b=-1):
		if b==-1: b=len(self.objs)
		for x in self.objs[a:b]:
			T=x['TYPE']
			if T in self.Type: TT=self.Type[T]
			else: TT="??? (%s)"%(binascii.hexlify(T))
			if TT in ['BOUNDARY','PATH','SREF','AREF','TEXT','NODE','BOX']:
				print("[", TT, "]")
			else:
				print("\t[",TT,"]", x['PARAMS'])
	def getLobjs(self,a=0,b=-1):
		r=[]
		co={}
		if b==-1: b=len(self.objs)
		for x in self.objs[a:b]:
			T=x['TYPE']
			if T in self.Type: TT=self.Type[T]
			else: TT="??? (%s)"%(binascii.hexlify(T))
			if TT in ['BOUNDARY','PATH','SREF','AREF','TEXT','NODE','BOX']:
				if 'TYPE' in co:
					r.append(co)
				co={}
				co['TYPE']=TT
			else:
				co[TT]=x['PARAMS']
		if co!={}: r.append(co)
		return r
				
	def getstructs(self):
		r=[]
		for i in self.structs:
			s=self.objs[i[0]+1]['PARAMS'][0]
			if s[-1]=='\x00': s=s[:-1]
			r.append(s)
		return r
	def getstruct(self, s):
		for i in self.structs:
			ss=self.objs[i[0]+1]['PARAMS'][0]
			if ss[-1]=='\x00': ss=ss[:-1]
			if ss==s:
				return i
	def write(self,path):
		f=open(path,"wb")
		for x in self.objs:
			 f.write(self.encodeObj(x['TYPE'],x['PARAMS']))
		f.close()
	def addLine(self,pts, layer=0, width=0, dose=1,loop=None):
		if loop==None:
			loop=self.loops
		self.addObj('PATH')
		self.addObj('LAYER',layer)
		self.addObj('DATATYPE',self.doseEnc(dose))
		self.addObj('WIDTH',width)
		self.addObj('XY',pts)
		if loop>1:
			self.writeLoop(loop)
		# No idea what it is, but Raith write them for each line!
		# It doesn't work if this command is not set!
		self.addObj('\x11\x00')
	def playMacro(self):
		for x in self.macro:
			self.addObj(x['TYPE'],x['PARAMS'])
	def startMacro(self):
		self.macro=[]
		self.enabledMacro=True
	def stopMacro(self,type=None):
		self.enabledMacro=False
	def MatrixMacro(self,space,N):
		currentShift=self.shift
		for y in range(N[1]):
			for x in range(N[0]):
				self.playMacro()
				self.uvShift(x=space[0])
			self.uvShift(x=-space[0]*N[0],y=space[1])
		self.shift=currentShift
	def addObj(self,t,p=[]):
		if self.enabledMacro:
			self.macro.append({'TYPE':t,'PARAMS':p})
		else:
			if type(p)==str:
				if len(p)%2==1: p+'\x00'
			if type(p)!=list and type(p)!=tuple: p=[p]
			tt=self.getType(t)
			# \x10\x03 is the code for XY
			if tt=='\x10\x03':
				p=reduce(lambda x,y:x+y,map(lambda z: self.uv2xy(z),zip(p[::2],p[1::2])))
				for i in range(len(p[::2])):
					if p[::2][i]<self.area[self.currentStructure][0]: self.area[self.currentStructure][0]=p[::2][i]
					if p[::2][i]>self.area[self.currentStructure][2]: self.area[self.currentStructure][2]=p[::2][i]
					if p[1::2][i]<self.area[self.currentStructure][1]: self.area[self.currentStructure][1]=p[1::2][i]
					if p[1::2][i]>self.area[self.currentStructure][3]: self.area[self.currentStructure][3]=p[1::2][i]
			if self.f != None:
				self.f.write(self.encodeObj(tt,p))
			else:
				self.objs.append({'TYPE':tt,'PARAMS':p})
	def getArea(self, st):
		return self.area[st]
	def new(self,name='TEST'):
		self.objs=[]
		self.addObj('HEADER',3)
		self.addObj('BGNLIB',[2010,1,1,0,0,0,2010,1,1,0,0,0])
		self.addObj('LIBNAME',[name])
		self.addObj('UNITS',[0.001,1e-09])
	def newStr(self, name):
		self.shift=[0,0]
		self.currentStructure=name
		self.area[name]=[0,0,0,0]
		self.StrPos[name]=self.f.tell()
		self.addObj('BGNSTR',[2010,1,1,0,0,0,2010,1,1,0,0,0])
		self.addObj('STRNAME',name)
	def endStr(self):
		self.addObj('ENDSTR')
	def endLib(self):
		self.addObj('ENDLIB')
	def addCircle(self, pos, radius, npts=10, layer=0, width=0, dose=1, A=0, B=360,loop=None):
		if loop==None:
			loop=self.loops
		coords=[]
		A*=math.pi/180
		B*=math.pi/180
		for i in range(npts+1):
			x=pos[0]+radius*math.cos(A+(B-A)*i/npts)
			y=pos[1]+radius*math.sin(A+(B-A)*i/npts)
			coords+=[x,y]
		self.addLine(coords,dose=dose,width=width,layer=layer)
		if loop>1:
			self.writeLoop(loop)
	def close(self):
		self.f.close()
	def addPoly(self, pos, layer=0, dose=1,loop=None,fmode=None,dmode=None, adir=None):
		if loop==None:
			loop=self.loops
		if pos[-2]!=pos[0] or pos[-1]!=pos[1]:
			pos+=pos[0:2]
		# pos=[x1,y1,x2,y2,x3,y3,...,x1,y1]
		self.addObj('BOUNDARY')
		self.addObj('LAYER',layer)
		self.addObj('DATATYPE',self.doseEnc(dose))
		self.addObj('XY',pos)
		if loop>1:
			self.writeLoop(loop)
		if fmode!=None:
			self.writeFillMode(fmode)
		if dmode!=None:
			self.writeDirMode(dmode)
		if adir!=None:
			self.writeAngleDir(adir)
		self.addObj('\x11\x00')
	def addRect(self, pos, layer=0, dose=1,CCW=False,loop=None):
		if loop==None:
			loop=self.loops
		# pos=[x,y,w,h]
		if CCW:
			self.addPoly([pos[0],pos[1],pos[0]+pos[2],pos[1],pos[0]+pos[2],pos[1]+pos[3],pos[0],pos[1]+pos[3],pos[0],pos[1]],dose=does,layer=layer,loop=loop)
		else:
			self.addPoly([pos[0],pos[1],pos[0],pos[1]+pos[3],pos[0]+pos[2],pos[1]+pos[3],pos[0]+pos[2],pos[1],pos[0],pos[1]],dose=dose,layer=layer,loop=loop)
	def addText(self, pos, txt, height=None, mag=22.22222, layer=0, width=0, dose=1,angle=0,loop=None, align='NW',custom=False, mirror=False):
		# Custom Font
		font={	'0':[[(0,0),(1,0),(1,2),(0,2),(0,0)]],
			'1':[[(.5,0),(.5,2)]],
			'2':[[(0,2),(1,2),(1,1),(0,1),(0,0),(1,0)]],
			'3':[[(0,0),(1,0),(1,2),(0,2)],[(0,1),(1,1)]],
			'4':[[(0,2),(0,1),(1,1)],[(1,2),(1,0)]],
			'5':[[(0,0),(1,0),(1,1),(0,1),(0,2),(1,2)]],
			'6':[[(1,2),(0,2),(0,0),(1,0),(1,1),(0,1)]],
			'7':[[(0,2),(1,2),(0,0)],[(0,1),(1,1)]],
			'8':[[(0,1),(1,1),(1,2),(0,2),(0,0),(1,0),(1,1)]],
			'9':[[(0,0),(1,0),(1,2),(0,2),(0,1),(1,1)]],
			'A':[[(0,0),(0,2),(1,2),(1,0)],[(0,1),(1,1)]],
			'B':[[(0,0),(0,2),(1,1.5),(0,1),(1,0.5),(0,0)]],
			'C':[[(1,0),(0,0),(0,2),(1,2)]],
			'D':[[(0,0),(0,2),(1,1),(0,0)]],
			'E':[[(1,0),(0,0),(0,2),(1,2)],[(0,1),(1,1)]],
			'F':[[(0,0),(0,2),(1,2)],[(0,1),(1,1)]],
			'G':[[(1,2),(0,2),(0,0),(1,0),(1,1),(0.5,1)]],
			'H':[[(0,0),(0,2)],[(1,0),(1,2)],[(0,1),(1,1)]],
			'I':[[(0.5,0),(0.5,2)],[(0,0),(1,0)],[(0,2),(1,2)]],
			'J':[[(0,2),(1,2),(1,0),(0,0),(.5,.5)]],
			'K':[[(0,0),(0,2)],[(1,2),(0,1),(1,0)]],
			'L':[[(0,2),(0,0),(1,0)]],
			'M':[[(0,0),(0,2),(0.5,1),(1,2),(1,0)]],
			'N':[[(0,0),(0,2),(1,0),(1,2)]],
			'O':[[(0,0),(1,0),(1,2),(0,2),(0,0)]],
			'P':[[(0,0),(0,2),(1,2),(1,1),(0,1)]],
			'Q':[[(0.5,0.5),(1,0),(1,2),(0,2),(0,0),(1,0)]],
			'R':[[(0,0),(0,2),(1,2),(1,1),(0,1),(1,0)]],
			'S':[[(0,0),(1,0),(1,1),(0,1),(0,2),(1,2)]],
			'T':[[(0,2),(1,2)],[(0.5,0),(0.5,2)]],
			'U':[[(0,2),(0,0),(1,0),(1,2)]],
			'V':[[(0,2),(.5,0),(1,2)]],
			'W':[[(0,2),(0,0),(.5,1),(1,0),(1,2)]],
			'X':[[(0,0),(1,2)],[(0,2),(1,0)]],
			'Y':[[(0,2),(.5,1),(1,2)],[(.5,1),(.5,0)]],
			'Z':[[(0,2),(1,2),(0,0),(1,0)]],
			'+':[[(0.5,0),(0.5,2)],[(0,1),(1,1)]],
			'-':[[(0,1),(1,1)]],
			'=':[[(0,.75),(1,.75)],[(0,.25),(1,.25)]],
			'.':[[(.33,0),(.33,.33),(.66,.33),(.66,0),(.33,0)]],
			'?':[[(0,0),(1,2),(0,2),(0,0),(1,0),(1,2)],[(0,2),(1,0)]],
			' ':[]
			}
		# height is given in micron!
		if loop==None:
			loop=self.loops
		if height!=None:
			mag=height*22.22222
		if not custom:
			self.addObj('TEXT')
			self.addObj('LAYER',layer)
			self.addObj('TEXTTYPE',0)
			self.addObj('DATATYPE',self.doseEnc(dose))
			al={'NW':0,'N':1,'NE':2,'W':4,'C':5,'E':6,'SW':8,'S':9,'SE':10}
			if type(align)==type(1):
				self.addObj('\x17\x02',align)
			else:
				self.addObj('\x17\x02',al[align])
			self.addObj('WIDTH',width)
			self.addObj('STRANS',0)
			if angle!=0:
				self.addObj('ANGLE',angle*1.0)
			self.addObj('MAG',mag)
			self.addObj('XY',pos)
			self.addObj('ASCII STRING',txt+'\x00')
			if loop>1:
				self.writeLoop(loop)
			self.addObj('\x11\x00')
		else:
			bckShift=self.shift
			bckMatr=self.M
			length=2*len(txt)-1
			self.uvShift(x=pos[0],y=pos[1])
			dx=length/2.0
			dy=height/2.0
			if 'W' in align:
				dx=0
			elif 'E' in align:
				dx=-length
			if 'N' in align:
				dy=0
			elif 'S':
				dy=-height
			if angle!=0:
				self.uvRotate(angle)
			if mirror:
				self.uvMirror(x=True)
				dx-=length
			self.uvScale(x=500*height,y=500*height)
			for x in enumerate(txt):
				t='?'
				if x[1] in font:
					t=x[1]
				else:
					if x[1].upper() in font:
						t=x[1].upper()
				for k in font[t]:
					self.addLine(reduce(lambda a,b: list(a)+list(b), map(lambda z: (dx+z[0]+x[0]*2,dy+z[1]),k)),dose=dose,layer=layer,loop=loop,width=width)
			self.M=bckMatr
			self.shift=bckShift
			
if __name__ == "__main__":
	## Exemple. Do a grating
	# create the GDSII object
	g=GDSII()
	if len(sys.argv)>1:
		g.open(sys.argv[1])
#		g.show()
	else:
		# add automatically the standard headers
		g.new('TEST')
		# add a new structure called "grating_test"
		g.newStr('grating_test')
		d=1
		for x in range(0,20000,800):
			# add one line with a dose d
			g.addLine((x,0,x,10000),dose=d)
			d+=1
		# Finish the structure (obligatory)
		g.endStr()
		g.newStr('triangle')
		g.addLine((0,0,100,0,0,100,0,0))
		g.endStr()
		g.newStr('circle_test')
		# Different radius and segement per circle
		g.addCircle((1000,1000),100,5)
		g.addCircle((1000,1000),200,10)
		g.addCircle((1000,1000),300,15)
		g.addCircle((1000,1000),400,20)
		g.addCircle((1000,1000),500,25)
		# Pentagons with different start angle
		g.addCircle((1000,2000),100,5)
		g.addCircle((1000,2000),200,5,A=20,B=380)
		g.addCircle((1000,2000),300,5,A=40,B=400)
		g.addCircle((1000,2000),400,5,A=60,B=420)
		# 1/4 circles
		g.addCircle((1000,3000),500,A=90,B=0)
		g.addCircle((2000,3000),500,A=180,B=360)
		g.addCircle((3000,3000),500,A=180,B=0)
		g.endStr()
		g.newStr('Poly_test')
		g.addRect((0,15000,1500,400))
		g.addRect((1900,15000,1500,400))
		g.addPoly((0,0,10000,0,10000,10000,0,10000,0,2000,2000,2000,2000,8000,8000,8000,8000,2000,0,2000,0,0))
		g.endStr()
		g.newStr('Text_test')
		y=0
		for m in enumerate([43.111,54.222,66.666,88.888]):
			g.addText((0,y),"ABCDEF",mag=m[1])
			y+=1000*(m[0]+1)
		g.endStr()
		# End the file (obligatory)
		g.endLib()
		# Display ASCII form of what was done (more for debuging purpose)
		##g.show()
		# Save the GDS to file
		g.write('test.gds')
