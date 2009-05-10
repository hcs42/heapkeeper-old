#!/usr/bin/python

import sys

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

sd /= count - 1

print "average: %f, SD: %f" % (avg, sd)
