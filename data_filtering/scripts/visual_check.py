"""
Some analysis on the beepath real data
"""

# imports #
import numpy as np
import beepath_science as bps 
import ula_funcs as uf
import os

mapdir= '../maps'

try:
	os.mkdir(mapdir)
except OSError:
	pass

# funcs #
#def parser(string):
#   ss = string[:-1].split(',')
#   return np.array([int(ss[1].split('"')[1]),float(ss[2].split('"')[1]),float(ss[3].split('"')[1]),bps.formats.string_to_UNIX([ss[4].split('"')[1]])[0],
#       float(ss[5].split('"')[1])]) #user_id, lon, lat , time UNIX, accuracy
def parser2(string):
    ss = string[:-1].split(' ')
    time = bps.formats.string_to_UNIX([' '.join(ss[4:6])])
    return np.r_[int(ss[1]),float(ss[2]),float(ss[3]),time,float(ss[6])] #user_id, lon, lat , time UNIX, accuracy

        
def generate_trac(xyt,Rf=8,Rs=8):
    """ generates trac and flights """
    sm = bps.models.stopormove(xyt,Rs)
    return bps.models.rectangularmodel(sm,Rf,Rs)

# paths #
data_path = '../dumps/filtered_updates.csv'
user_path = '../dumps/filtered_users.csv'

#opts #
latex = True

# load data
with open(user_path,'r') as f:
    us = f.readlines()
with open(data_path,'r') as f:
    rr = f.readlines()
qq = [int(e.split(' ')[0]) for e in us]
data = np.empty((len(rr),5))
for i,l in enumerate(rr):
    data[i] = parser2(l)


#with open(user_path,'r') as f:
#   us = f.readlines()
#qq = [int(e[1:4]) for e in us]
#with open(data_path,'r') as f:
#   rr = f.readlines()
#data = np.empty((len(rr),5))
#for i,l in enumerate(rr):
#   data[i] = parser(l)


# params #
Rs = 8
Rf = 8
bbox_x = 330
bbox_y = 145
origin = bps.constants.origin
zone = bps.constants.zone

## data checks ##
print "Unique users: %d"  % len(np.unique(qq))

# split in users #
acc_mean = []
acc_std = []
tracs = []
ts = []
fs = []
st = []
ups = []
ids = []
freq = []
for u in qq:
    ds = np.array(tuple(e for e in data if e[0]==u))
    xy = bps.geodesics.latlon_2_UTM(np.array([ds.T[1],ds.T[2]]).T,origin,zone,time=False)
    ups.append(len(xy))
    ds.T[1]=xy.T[0]
    ds.T[2]=xy.T[1]
    ds = ds.T[1:].T
    ds = bps.geometrics.crop_points_box(ds, bbox_x, bbox_y, -np.pi/4., (0,0))
    freq.append(np.ediff1d(ds.T[-2]))
    if len(ds)>0:
        acc_mean.append(ds.T[-1].mean())
        acc_std.append(ds.T[-1].std())
        ts.append(np.max(ds.T[-2])-np.min(ds.T[-2]))
        xyt = np.array([ds.T[0],ds.T[1],ds.T[2]]).T #lon lat points
        tracs.append(generate_trac(xyt))
        ids.append(u)
        fs.append(tracs[-1].N_flights)
        st.append(tracs[-1].N_stops)

## average point stats ##
freq = np.array(tuple(np.mean(ffreq) for ffreq in freq))

if latex:
	with open('visual_check.log','w') as f:
		print >>  f, "Update freq. $\\nu$ (s) 		&$%.3f \pm %.3f$ & $%.3f$ & $%.3f$ \\\ " 		% (np.mean(freq),np.std(freq),np.median(freq),(np.median(freq)-np.mean(freq))/np.mean(freq))
		print >>  f, "Average accuracy (m)  &$%.3f \pm %.3f$ & $%.3f$ & $%.3f$ \\\ " 		% (data.T[-1].mean(), data.T[-1].std(),np.median(data.T[-1]),
			(np.median(data.T[-1])-data.T[-1].mean())/data.T[-1].mean()) # average accuracy 
		print >>  f, "Number of updates per user. $N_{points}$ (-) & $%.3f \pm %.3f$ & $%.3f$ & $%.3f$ \\\ " 		% (np.mean(ups),np.std(ups),np.median(ups),(np.median(ups)-np.mean(ups))/np.mean(ups)) # average accuracy 
		print >> f, "Total time per user $T$ (minutes) & $%.3f \pm %.3f$ & $%.3f$ & $%.3f$ \\\ " %  (np.mean(ts)/60.,np.std(ts)/60,np.median(ts)/60,(np.median(ts)-np.mean(ts))/np.mean(ts)) # average time per user
		print >>  f, "Number of Flights (-) & $%.3f \pm %.3f$ & $%.3f$ & $%.3f$ \\\ " % (np.mean(fs),np.std(fs),np.median(fs),(np.median(fs)-np.mean(fs))/np.mean(fs))		
		print >>  f, "Number of Stops (-)   & $%.3f \pm %.3f$ & $%.3f$ & $%.3f$ \\\ " % (np.mean(st),np.std(st),np.median(st),(np.median(st)-np.mean(st))/np.mean(st))
		#print >>  f, "Flight duration $\overline{\Delta t_f}$(s) &$%.3f \pm %.3f$ & $%.3f$ & $%.3f$ \\\ " 
		ftt = np.array([t.v()[0] for t in tracs])
		print >>  f, "Flight velocity $line{v}$(m/s) 	 		&$%.3f \pm %.3f$ & $%.3f$ & $%.3f$ \\\ " 		% (np.mean(ftt),np.std(ftt),np.median(ftt),(np.median(ftt)-np.mean(ftt))/np.mean(ftt))
		fl = np.array([np.mean(tuple(t.iter_flights('Delta_r'))) for t in tracs])
		print >>  f, "Flight length $\Delta r_f$	(m)	 &$%.3f \pm %.3f$ & $%.3f$ & $%.3f$ \\\ " 		% (np.mean(fl),np.std(fl),np.median(fl),(np.median(fl)-np.mean(fl))/np.mean(fl))
		stt = np.array([np.mean(tuple(t.iter_stops('Delta_t'))) for t in tracs])
		print >>  f, "Stop duration $\overline{\Delta t_s}$	(s) &$%.3f \pm %.3f$ & $%.3f$ & $%.3f$ \\\ " 		% (np.mean(stt),np.std(stt),np.median(stt),(np.median(stt)-np.mean(stt))/np.mean(stt))
		#gg = np.array([t.rgyr()[0] for t in tracs])
		#print >>  f, "$%.3f \pm %.3f$ & $%.3f$ & $%.3f$ \\\ " 		% (np.mean(gg),np.std(gg),np.median(gg),(np.median(gg)-np.mean(gg))/np.mean(gg))
else:
	with open('visual_check.log','w') as f:
		print >> f,"# Average update freq [s]:		%f +- %f | %f" % (np.mean(freq),np.std(freq),np.median(freq))
		print >> f,"# Average accuracy [m]:	 		%f +- %f | %f" % (data.T[-1].mean(), data.T[-1].std(),np.median(data.T[-1])) # average accuracy 
		print >> f,"# Average ups [-]:		 		%f +- %f | %f" % (np.mean(ups),np.std(ups),np.median(ups)) # average accuracy 
		print >> f,"# Average time per user [min]: 	%f +- %f| %f" % (np.mean(ts)/60.,np.std(ts)/60,np.median(ts)/60) # average time per user
		print >> f,"# Average number of flights [-]: %f +- %f| %f" % (np.mean(fs),np.std(fs),np.median(fs))
		print >> f,"# Average number of stops [-]: 	%f +- %f| %f" % (np.mean(st),np.std(st),np.median(st))
		print >> f,"# Average flight velocity [m/s]: %f +- %f| %f" % (np.mean([t.v()[0] for t in tracs]),np.std([t.v()[0] for t in tracs]),np.median([t.v()[0] for t in tracs]))
		print >> f,"# Average flight length [m]: 	%f +- %f| %f" % (np.mean([np.mean(tuple(t.iter_flights('Delta_r'))) for t in tracs]),
			np.std([np.mean(tuple(t.iter_flights('Delta_r'))) for t in tracs]),np.median([np.mean(tuple(t.iter_flights('Delta_r'))) for t in tracs]))
		print >> f,"# Average stop duration [s]: 	%f +- %f| %f" % (np.mean([np.mean(tuple(t.iter_stops('Delta_t'))) for t in tracs]),
			np.std([np.mean(tuple(t.iter_stops('Delta_t'))) for t in tracs]),np.median([np.mean(tuple(t.iter_stops('Delta_t'))) for t in tracs]))
		print >> f,"# Average user rgyr [m]: 		%f +- %f| %f" % (np.mean([t.rgyr()[0] for t in tracs]),np.std([t.rgyr()[0] for t in tracs]),np.median([t.rgyr()[0] for t in tracs]))
	

## aggregate trace ##
z=0
c=0
superT = bps.classes.Trace()
for po,t in enumerate(tracs):
    for f in t.iter_flights():
        f.user = ids[po]
        superT.add_flight(f)
    for j,s in enumerate(t.iter_stops()):
        if j != 0 and j != (t.N_stops - 1):
            superT.add_stop(s)
        else:
            if s.Delta_t > 0:
                superT.add_stop(s)

## long flights ##
dict_tracs = dict(zip(ids,tracs))

def time_start(fl,trac):
	 mm = np.min([t[0][-1] for t in trac.iter_flights('StartEnd')])
	 m  = np.max([t[-1][-1] for t in trac.iter_flights('StartEnd')])
	 return mm,m-mm

longs = []
inf = []
R_max = 60
for f in superT.iter_flights():
    if f.Delta_r>R_max:
        longs.append(f)
        inf.append([f.N_points,f.Delta_r,f.Delta_t,f.user,len(tuple(e for e in superT.iter_flights('user') if e==f.user)),
        f.StartEnd[0][-1]-time_start(f,dict_tracs[f.user])[0],time_start(f,dict_tracs[f.user])[1]])

np.savetxt('longflights.info',inf,header='#Flights larger than 60 mtrs: N_points in flight\tDelta_r\tDelta_t\tUser_id\tTotal_flights_user\tTime_after_1st_flight\tTotal_user_time')

# long flights plot #
import pylab as pl
xy = [bps.geometrics.rotate_xyt(f.UTM,np.pi/4.) for f in longs]
pl.clf()
ax = pl.subplot(1,1,1)
for e in xy:
    ax.plot(e.T[0],e.T[1],'.',color='blue')
    st = np.array([[e[0][0],e[0][1]],[e[-1][0],e[-1][1]]])
    ax.plot(st.T[0],st.T[1],'-',color='grey',linewidth=2)
ax.set_aspect('equal', adjustable='box')
ax.set_xlabel('Rotated x [m]')
ax.set_ylabel('Rotated y [m]')
ax.set_xlim(xmin=0,xmax=350)
ax.set_ylim(ymin=0,ymax=150)
pl.savefig('Long_flights.png')
# save coords too #
xyy = np.array([f.StartEnd for f in longs]).flatten().reshape(len(longs),6)

np.savetxt('longflights.xy',xyy,header='# Flights larger than 60 mtrs: Start and ending point \n # Lon_start Lat_start Timestamp_start Lon_stop Lat_stop Timestamp_stop')

# long flights CDF time #
import ula_funcs as uf
inff=np.array(inf)
rel = inff.T[-2]/inff.T[-1]
pl.clf()
q = uf.stats.pdf(rel)
pl.plot(q[-1][0],q[-1][-1],'o')
pl.plot(q[-1][0],1.-q[-1][0],'--',color='k')
pl.xlabel('Relative time from start of movement')
pl.ylabel('CCDF')
pl.savefig('Long_flights_time.png')


# Example algorithm plot #
def quickview(points,tracs,ang,path=None):
    """ generates quick plot of points and flights 
    Input:
        Points: Raw points in x,y
        Tracs: LIst of 3 model tracks [Rect, Angular, Pause]
        Path: Path to save image
    
    """
    styles=('-','--',':')
    names=('rect','angular','pause')
    colors=('g','grey','b')
    pl.clf()
    ax = pl.subplot(111)
    tdum = range(len(points)) # dummy time
    points = np.vstack((points.T,tdum)).T
    points = bps.geometrics.rotate_xyt(points,ang)
    ax.plot(points.T[0],points.T[1],'o',label='raw_points',alpha=0.8,color=colors[-1])
    i=0
    maxs=5
    for tr in tracs:
        for q,fl in enumerate(tr.iter_flights()):
            if q == 0:
                lab = 'Flights'
            else:
                lab = None
            ps = bps.geometrics.rotate_xyt(fl.StartEnd,ang)
            ax.plot(ps.T[0],ps.T[1],styles[i],label=lab,color=colors[-2],lw=2.)
        for fl in tr.iter_stops():
            if q == 0:
                lab = 'Stops'
            else:
                lab = None
            ps = bps.geometrics.rotate_xyt([fl.mean_point],ang)
            #circle1=pl.Circle([ps.T[0],ps.T[1]],fl.N_points/10.,edgecolor=colors[i],facecolor=None,color=colors[i],alpha=0.1)
            #ax.add_artist(circle1)
            ax.plot(ps.T[0],ps.T[1],'o',label=lab,color=colors[i],markersize=fl.N_points*1./maxs*3.,alpha=0.5)
            ax.plot(ps.T[0],ps.T[1],'x',color='k',label=l)
        i+=1
    ax.set_xlabel('Rotated x [m]')
    ax.set_ylabel('Rotated y [m]')
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(xmin=0,xmax=350)
    ax.set_ylim(ymin=0,ymax=150)
    #pl.legend(loc='best')
    #ax.set_aspect('equal', adjustable='box')
    #pl.legend(loc='best')
    if path: pl.savefig(path)
    else: pl.show()

#points = superT.allpoints()
#points = tracs[23].allpoints()
# fix this shit!
for q,tr in enumerate(tracs):
    points = tr.allpoints()
    traczs = [tr]
    patht = mapdir+'/map'+str(q)+'.png'
    quickview(points,traczs,np.pi/4,patht)
