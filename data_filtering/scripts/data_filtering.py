#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    Filtering algortihm to apply to published data 
        input: "BeePath2012_nomails.sqp"
        
    Applies:
        User filtering
"""

### Modules ###

import MySQLdb as mdb
#import pymysql as mdb
import numpy as np
import beepath_science as bps
import os
import pylab as pl

### General variables definition ###

bps.constants.zone=31 # zone utm 31T
bps.constants.origin=(431769,4582211) # map origin, Coordenades geodèsiques: N41º23.312 E02º11.034
bps.constants.eps=0.0000001 # very small value (to avoid problems)

zone=bps.constants.zone
origin=bps.constants.origin
eps=bps.constants.eps
utm=bps.constants.utm()


# opts
# database selection
max_cache=int(5e5)
usr='root' #myuser
passw='' # mypass
datab='BeePath2012_filtered'
#server='localhost'
server='127.0.0.1'
output = '../dumps/'

# point selection
min_acc = 6
#flight selection 
min_updats = 4 #(1minute)
min_flights = 4 # (statistical accuracy)
v_max=50/3.6 # in m/s max . Velocity of 30km/h
min_freq=180. # 180 seconds

# flight generation
R_st=8. # stop-or-move model param
R_mv=8. # rectangular model param
theta_mv=30. # angular model param


### Funcs


def count_entries(entry,table):
    action = 'SELECT COUNT(%s) from %s' %  (entry,table)
    cur.execute(action)
    return cur.fetchall()[0]
def count_entries_distinct(entry,table):
    action = 'SELECT COUNT(DISTINCT(%s)) from %s' %  (entry,table)
    cur.execute(action)
    return cur.fetchall()[0]







### Start! : Connect database
db=mdb.connect(server,usr,passw,local_infile=1)
cur=db.cursor()
cur.execute('USE %s' % datab)

########## Accuracy clean #########
print "### Accuracy cleaning"
l = count_entries('id','paths')
cur.execute('delete from paths where accuracy > %f' % min_acc) 
l2 = count_entries('id','paths')
print "\t Deleted %d, frac:%f" % (l[0]-l2[0],(l[0]-l2[0])*1./l[0])


#user list
cur.execute('SELECT distinct(id_user) from paths')
paths=[ int(e[0]) for e in cur.fetchall()]
# delete users from databse that have no valid paths
cur.execute('SELECT distinct(id) from userInfo')
all_users=[ int(e[0]) for e in cur.fetchall()]
user_2_delete=list(set(all_users).difference(paths))
#[u for u in all_users if u not in paths]
print "### User cleaning matching paths and userInfo lists###"
for u in user_2_delete: cur.execute('delete from userInfo where id=%r' % u)






# Manage folders
try:
    os.mkdir(output)
except:
    pass


## get data and tracs
cur.execute('SELECT distinct(id_user) from paths') # all data
paths=[int(e[0]) for e in cur.fetchall()]

for user in paths:
    cur.execute('SELECT lon,lat,UNIX_TIMESTAMP(timestamp) from paths WHERE id_user=%r ORDER BY UNIX_TIMESTAMP(timestamp) '% (user))
    updats=np.array([np.array(e,dtype=float) for e in cur.fetchall()])
    ### flags ### --> enough updates
    flag = False
    if len(updats)<min_updats:
        flag = True
    else:
        ##convert to utm
        up=bps.geodesics.latlon_2_UTM(updats,origin,zone,time=True)
        ## apply velocity filter (rough)
        ch=len(up)
        ups=bps.filters.filter_v_updates(up,v_max=v_max,zone=zone,UTM=True)
        print "Eliminated points %r from original %r" % (ch-sum(e.shape[0] for e in ups),ch)
        ## generate tracs ##
        trac_rect=[]
        for up in ups: # Groups of updates
            ## apply stop or move model ##
            #points=bps.models.stopormove_v(up,R_st,T_st,T_st_max) # just stops in time, not applying model
            points = bps.models.stopormove(up,R_st) # apply simple filter
            ## apply rect model (rect, angular, pause) 
            trac_rect.append(bps.models.rectangularmodel(points,R_mv,R_st))
        trac_rect=np.sum(trac_rect) # Sum all traces
        trac_angle=bps.models.angularmodel(trac_rect,theta_mv)
        trac_pause=bps.models.pausemodel(trac_rect)
        # Once we have the tracs, keep only those with enough flights and short enough update_freq (using rect model)
        #if trac_rect.N_flights>min_flights and trac_rect.update_freq()[0][0] < min_freq :
        if trac_rect.N_flights>min_flights:
            pass
        else:
            flag = True
    if flag: # if flag goes off, delete updates and user
        cur.execute('DELETE FROM paths WHERE id_user=%r' % user)
        cur.execute('DELETE FROM userInfo WHERE id=%r' % user)

### print raw files ###
cur.execute('SELECT * FROM paths')
updates = [map(str,e) for e in cur.fetchall()]
cur.execute('SELECT * FROM userInfo')
users = [map(str,e) for e in cur.fetchall()]

fields = len(updates[0])
np.savetxt(output+'filtered_updates.csv',updates,fmt='%s '*fields)
fields = len(users[0])
np.savetxt(output+'filtered_users.csv',users,fmt='%s '*fields)


db.close()
print "## Now it would be the time to backup! ##"

### create backup  ###
os.system("/opt/lampp/bin/mysqldump -uroot %s > %s" % (datab,output+datab+'.sql'))


