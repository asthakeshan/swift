from sbp.client.drivers.pyserial_driver import PySerialDriver
from sbp.client import Handler, Framer
from sbp.client.loggers.json_logger import JSONLogger
from sbp.navigation import *
import argparse

from iobeam import iobeam
import time

PROJECT_ID = 403 # int
PROJECT_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6MjkyNn0=.eyJwaWQiOjQwMywiY3J0IjoxNDcwNDI2OTk0LCJleHAiOjE0NzgyMDI5OTQsInBtcyI6N30=.sTVlxfqQTbQpiET2NBNZfook8TR--s4DKDwXXrrfGFo=" # String
DEVICE_ID = "my-first-device"

# Init iobeam
builder = iobeam.ClientBuilder(PROJECT_ID, PROJECT_TOKEN).saveToDisk()
builder.registerOrSetId(DEVICE_ID)
iobeamClient = builder.build()
store_baseline = iobeamClient.createDataStore(["N", "E", "D"])
store_position = iobeamClient.createDataStore(["Lat", "Lon", "alt", "NumSats"])



def baseline_callback_ned(sbp_msg, **metadata):
  now = int(time.time() * 1000)
  print "baseline:"
  soln = MsgBaselineNED(sbp_msg)
  store_baseline.add(iobeam.Timestamp(now), {"N": soln.n *1e-3,
                                              "E": soln.e *1e-3,
                                              "D": soln.d *1e-3})
  iobeamClient.send()
  print "%.4f,%.4f,%.4f" % (soln.n * 1e-3, soln.e * 1e-3, soln.d * 1e-3)


def pos_llh_callback(sbp_msg, **metadata):
  now = int(time.time() * 1000)
  print "position:"
  soln = MsgPosLLH(sbp_msg)
  store_position.add(iobeam.Timestamp(now), {"Lat": soln.lat,
                                              "Lon": soln.lon,
                                              "alt": soln.height,
                                              "NumSats": soln.n_sats})
  iobeamClient.send()
  print "%.10f,%.10f" % (soln.lat, soln.lon)

def main():
  parser = argparse.ArgumentParser(description="Swift Navigation SBP Example.")
  parser.add_argument("-p", "--port",
                      default=['/dev/ttyUSB0'], nargs=1,
                      help="specify the serial port to use.")
  args = parser.parse_args()

  # Open a connection to Piksi using the default baud rate (1Mbaud)
  with PySerialDriver(args.port[0], baud=1000000) as driver:
    with Handler(Framer(driver.read, None, verbose=True)) as link:
      link.add_callback(baseline_callback_ned, SBP_MSG_BASELINE_NED)
      link.add_callback(pos_llh_callback, SBP_MSG_POS_LLH)
      link.start
      try:
        while True:
          time.sleep(0.1)
      except KeyboardInterrupt:
        pass

if __name__ == "__main__":
  main()
