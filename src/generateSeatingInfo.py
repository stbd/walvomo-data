import sys
import codecs
import dataProcessingLib

if len(sys.argv) != 4:
    print 'Usage: ' + sys.argv[0] + ' <file-to-excel-cvs-exported-seating> <reps-json> <json-seatfile>'
    sys.exit(1)

f = codecs.open(sys.argv[1], 'r', 'utf-8')
repsFile = codecs.open(sys.argv[2], 'r', 'utf-8')
seatFile = codecs.open(sys.argv[3], 'w', 'utf-8')
reps = dataProcessingLib.Representatives()
reps.parseFromFile(repsFile)
seating = dataProcessingLib.SeasonSeating()

while 1:
    r1 = f.readline().strip()
    r2 = f.readline().strip()
    r3 = f.readline().strip()

    if len(r1) == 0 or len(r2) == 0 or len(r3) == 0:
        break
    
    s1 = r1.split(';')
    s2 = r2.split(';')
    s3 = r3.split(';')
    
    for i in range(len(s1)):
        s1[i].strip()
        if len(s1[i]) != 0 and len(s2[i]) != 0 and len(s3[i]) != 0:
            id = reps.findRepresentativeId(s2[i], s3[i])
            print 'Seat:', s1[i], 'name:', s2[i], s3[i], 'id:', id
            seating.listOfIdSeatPairs[int(id)] = int(s1[i])
#print seating.data['IdToSeat']
seating.saveToFile(seatFile)

            
