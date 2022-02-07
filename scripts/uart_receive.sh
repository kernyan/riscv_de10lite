#! /usr/bin/env python3
import usb1

if __name__ == '__main__':
  with usb1.USBContext() as context:
    handle = context.openByVendorIDAndProductID(
      0x0403, 0x6001, skip_on_error=True)
    if handle is None:
      print('not detected')
    else:
      dev = handle.getDevice()

      for i in range(8):
        try:
          print(i, dev.getMaxPacketSize(i))
        except:
          pass

      for i in range(8):
        try:
          print(i, handle.bulkRead(i, 64))
        except:
          pass
