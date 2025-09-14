import sys
import time, datetime

class ProgressBar:
  def __init__(self, end, length=60, stream=sys.stderr):
    self.end = end
    self.length = length
    self.count = 0
    self.stream = stream

    self.start = time.time()
    self.last_printed_time = self.start

    self.stream.write(str(self))
  
  def increment(self):
    percent = 100 * self.count / self.end
    next_percent = 100 * (self.count + 1) / self.end

    calc_size = lambda c: int(round(float(self.length) / self.end) * c)
    size = calc_size(self.count)
    next_size = calc_size(self.count + 1)

    curr_time = time.time()
    print_time_delta = curr_time - self.last_printed_time

    self.count += 1
    if next_size != size or percent != next_percent or print_time_delta > 1:
      self.last_printed_time = curr_time
      self.stream.write(str(self))

  def __str__(self):
    try:
      running_sec = self.last_printed_time - self.start
      speed = float(self.count) / running_sec
      remaining_sec = (self.end - self.count) / speed
      eta = datetime.timedelta(seconds=int(round(remaining_sec)))
    except ZeroDivisionError:
      eta = '-:--:--'

    x = float(self.count) / self.end
    progress = int(round(x * self.length)) * '#'
    return '\r[{progress:<{max}}] {percent:3.0f} % ETA ({eta})'.format(
        progress=progress, max=self.length, percent = x*100, eta = eta)
