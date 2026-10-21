SELECT 
    ticid, ra, dec, pmra, pmdec, rad, mass, teff, tess_mag
FROM 
    dbo.ticv81
WHERE 
    rad BETWEEN 0.5 AND 0.7             #Interval chosen because its relating the transit depth so if its too low then a 
                                        #binary star causes the gap, but 0.5- 
                                        #0.7 is the perfect range

    AND teff BETWEEN 4000 AND 5000      #Cool and quiet stellar hosts
    AND tess_mag < 13.0                 #So this just measures the brightness so a lower brightness is important cause it indicates a gap
    AND priority > 0.8;                 #Priority is apparently a mix of attributes on a 0-1 scale for detecting planets so stuff like if the star is smaller                                          
                                        #like a red dwarf, it'll get more priority, because a small planet blocks a larger percentage of their light
