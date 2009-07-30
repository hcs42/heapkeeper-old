#!/usr/bin/python

import sys
import math

nums = []
count = 0
avg = 0
sd = 0

for x in sys.stdin:
    x = float(x)
    nums.append(x)
    avg += x
    count += 1

avg /= count

for x in nums:
    d = x - avg
    sd += d * d

sd = math.sqrt(sd / (count - 1))

print "average: %.2f s, SD: %.2f s." % (avg, sd)
