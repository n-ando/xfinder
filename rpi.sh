#!/bin/sh
#
# @file rpi.sh
# @brief RaspberryPi setup script for OpenRTM-aist
# @author Noriaki Ando <n-ando@aist.go.jp>
# @date 2013.05.15
#
packages="sysv-rc-conf avahi-daemon bc cmake subversion git"
iodev_packages="python-dev git-core i2c-tools python-smbus python-setuptools"

usage()
{
  echo "Usage: $0 hostname --type <TYPE>"
  echo ""
  echo "TYPE are:  basic kobuki kobuki_only rtunit rtunit_only"
  echo "  basic:           Installing avahi, cmake, subversion/git and OpenRTM"
  echo "  kobuki:          Installing basic + Kobuki RTC"
  echo "  kobuki_only:     Installing Kobuki RTC only"
  echo "  rtunit:          Installing basic + spi/i2c tools and modules"
  echo "  rtunit_only:     Installing spi/i2c tools and modules only"
  echo "  rtunit_examples: Installing basic + PiRT-Unit examples"
  echo ""
  echo "EXAMPLE:"
  echo "1) Just change hostname"
  echo "# rpi.sh kobuki0"
  echo ""
  echo "2) Basic setup: Installing OpenRTM-aist (C++/Python)"
  echo "# rpi.sh kobuki --type basic"
  echo ""
  echo "3) Kobuki setup: Installing OpenRTM-aist (C++/Python) and Kobuki RTC"
  echo "# rpi.sh kobuki --type kobuki"
  echo ""
}

set_hostname()
{
  tmp0=`grep $HOSTNAME /etc/hostname`
  tmp1=`grep $HOSTNAME /etc/hosts`
  if test "x" = "x$tmp0"; then
    echo $HOSTNAME > /etc/hostname
  fi
  if test "x" = "x$tmp1"; then
    sed -i 's/\(^127.0.1.1.*$\)/#\1/g' /etc/hosts
    echo "127.0.1.1\t$HOSTNAME" >> /etc/hosts
  fi
}

getopt()
{
  if test ! `id -u` = 0 ; then
    echo "Please run this script as root."
    exit 1
  fi
  if test $# -eq 0; then
    usage
    exit 1
  fi
  HOSTNAME=$1
  echo "HOSTNAME: $HOSTNAME"
  if test $# -eq 1; then
    set_hostname
    exit 0
  fi
  if test "x$2" = "x--type"; then
    TYPE=$3
  else
    echo "Invalid option"
    exit 1
  fi
  echo "Setyp type: $TYPE"
}

install_packages()
{
  echo "Installing basic packages"
  apt-get update
  apt-get -y install $packages
}

setup_wpa_supplicant()
{
  cat << EOF > /etc/wpa_supplicant/wpa_supplicant.conf
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
        ssid="OpenRTM"
        #psk="4332221111"
        psk=142914b76be167767055ff945898baaaf83c42b3ad3b99afb0ae531e8fb15e5e
}
network={
        ssid="OpenRTM-aist-G"
        #psk="aabbccddee"
        psk=94d37774a77090144461d40f51c4b3c11fc8ab397eac5c9ba59e04e02088cf4d
}
network={
        ssid="OpenRTM-aist-A"
        #psk="aabbccddee"
        psk=0e1435eee333431d935925fe773c83326dc9b44e5cb4484a4ba57c0199f84c95
}

EOF

}

setup_network_if()
{
  cat << EOF > /etc/network/interfaces
auto lo

iface lo inet loopback
allow-hotplug eth0
iface eth0 inet dhcp

auto wlan0
allow-hotplug wlan0
iface wlan0 inet dhcp
wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
EOF
  ifdown wlan0
  ifup wlan0
}

install_openrtm()
{
  rm -f pkg_install_debian.sh
  wget http://svn.openrtm.org/OpenRTM-aist/trunk/OpenRTM-aist/build/pkg_install_debian.sh
  sed -i 's/\(\/pub\/Linux\/debian\/\)/\/pub\/Linux\/raspbian\//' pkg_install_debian.sh
  sed -i 's/apt-get install/apt-get -y --force-yes install/g' pkg_install_debian.sh
  sudo sh pkg_install_debian.sh
  rm -f pkg_install_debian.sh
}

install_openrtm_python()
{
  rm -f pkg_install_python_debian.sh
  wget http://svn.openrtm.org/OpenRTM-aist-Python/trunk/OpenRTM-aist-Python/installer/install_scripts/pkg_install_python_debian.sh
  sed -i 's/\(\/pub\/Linux\/debian\/\)/\/pub\/Linux\/raspbian\//' pkg_install_python_debian.sh
  sed -i 's/apt-get install/apt-get -y --force-yes install/g' pkg_install_python_debian.sh
  sudo sh pkg_install_python_debian.sh
  rm -f pkg_install_python_debian.sh
}

#============================================================
# Kobuki
create_kobuki_sh()
{
  cat << EOF > /etc/kobuki.sh
#!/bin/sh
#
# KobukiAIST RTC launch script
#
#       Copyright Noriaki Ando <n-ando@openrtm.org>
#       2011.03.27
#
# This script should be executed from rc script like a rc.local
# as the following command line.
#
#

master=http://openrtm.org:8080
ns=/usr/bin/rtm-naming
kobukiRTC=/usr/lib/openrtm-1.1/rtc/KobukiAISTComp
workdir=/tmp/kobuki

\$ns
sleep 5

if test -d $workdir ; then
        echo ""
else
        mkdir \$workdir
fi

cd $workdir

while :
do
    rm -f \$workdir/*.log
    \$kobukiRTC
    sleep 5
done
EOF
  chmod 755 /etc/kobuki.sh
}

edit_rc_local()
{
  tmp=`grep '^exit 0' /etc/rc.local|wc|awk '{print $1}'`
  if test "x$tmp" = "x1"; then
    sed -i '/^exit/i\su - -c /etc/kobuki.sh 2>&1 | perl -p -e "s/\\n/\\r\\n/g" 1>&2 &' /etc/rc.local
  else
    echo "su - -c /etc/kobuki.sh 2>&1 | perl -p -e 's/\n/\r\n/g' 1>&2 &" >> /etc/rc.local
  fi
}

install_kobuki()
{
  basedir=`pwd`
  svn co http://svn.openrtm.org/components/trunk/mobile_robots/kobuki
  cd kobuki
  mkdir build
  cd build
  cmake -DCMAKE_INSTALL_PREFIX=/usr ..
  make
  cd src
  make install
  cd $basedir
  chown -R pi kobuki
}

#============================================================
# PiRT-Unit
install_iodev_packages()
{
  echo "Installing IO device support packages"
  apt-get update
  apt-get -y install $iodev_packages
  echo "Done"
}

setup_raspi_blacklist()
{
  echo "Modifying raspi-blacklist.conf"
  sed -i 's/\(^blacklist spi-bcm2708\)/#\1/' /etc/modprobe.d/raspi-blacklist.conf
  sed -i 's/\(^blacklist i2c-bcm2708\)/#\1/' /etc/modprobe.d/raspi-blacklist.conf
  echo "Done"
}

create_udev_rules()
{
  echo "Creating udev rules"
  cat << EOF > /etc/udev/rules.d/50-udev.rules
KERNEL=="spidev*", SUBSYSTEM=="spidev", GROUP="spi", MODE="0666"
EOF
  echo "Done"
}


install_pyspidev()
{
  echo "Installing pyspidev"
  basedir=`pwd`
  git clone git://github.com/doceme/py-spidev 
  cd py-spidev
  chmod 755 setup.py
  sudo ./setup.py install
  echo "done"
  cd $basedir
  chown -R pi py-spidev
}

install_wiringpi()
{
 echo "Installing WiringPi"
 basedir=`pwd`
 git clone git://git.drogon.net/wiringPi
 cd wiringPi
 git pull origin
 chmod 755 build
 ./build
 echo "done"
 cd $basedir
 chown -R pi wiringPi
}

install_wiringpi_py()
{
  basedir=`pwd`
  echo "Installing WiringPi python"
  git clone https://github.com/WiringPi/WiringPi-Python.git
  cd WiringPi-Python
  git submodule update --init
  sudo python setup.py install
  echo "done"
  cd $basedir
  chown -R pi WiringPi-Python
}

create_adc_test()
{
  mkdir -p ~pi/PiRT-Unit/
  chown pi ~pi/PiRT-Unit/
  cat << EOF > ~pi/PiRT-Unit/adc_test.py
#!/usr/bin/env python
# -*- coding: euc-jp -*-
import sys
import time
import spidev

class ADC:
  def __init__(self):
    self.spi = spidev.SpiDev()
    self.spi.open(0, 0)

  def get_value(self, channel):
    sned_ch = [0x00,0x08,0x10,0x18]
    if ((channel > 3) or (channel < 0)):
      return -1
    r = self.spi.xfer2([sned_ch[channel],0,0,0])
    ret = ((r[2] << 6 ) & 0x300) |  ((r[2] << 6) & 0xc0) | ((r[3] >> 2) & 0x3f)
    return ret

  def get_voltage(self, channel):
    ret = self.get_value(channel) * 5.0 / 1024
    return ret

def main():
  adc = ADC()
  while 1:
    adc1 = adc.get_value(0)
    msg1 = "%1.5fV(%04x)" % ((float(adc1)*5/1024),adc1)
    print msg1,

    adc1 = adc.get_value(1)
    msg1 = "%1.5fV(%04x)" % ((float(adc1)*5/1024),adc1)
    print msg1,

    adc2 = adc.get_value(2)
    msg2 = "%1.5fV(%04x)" % ((float(adc2)*5/1024),adc2)
    print msg2,

    adc3 = adc.get_value(3)
    msg3 = "%1.5fV(%04x)" % ((float(adc3)*5/1024),adc3)
    print msg3,

    sys.stdout.write("\n")
    time.sleep(0.5)

if __name__ == '__main__':
  main()
EOF
  chmod 755 ~pi/PiRT-Unit/adc_test.py
  chown pi ~pi/PiRT-Unit/adc_test.py
}

create_dac_test()
{
  mkdir -p ~pi/PiRT-Unit/
  chown pi ~pi/PiRT-Unit/
  cat << EOF > ~pi/PiRT-Unit/dac_test.py
#!/usr/bin/env python
# -*- coding: euc-jp -*- 
import spidev
from time import sleep

spi = spidev.SpiDev()
spi.open(0,1)

def changeLevel(ch,  onOff, percent):
  bit7 = ch    << 7
  bit6 = 0     << 6
  bit5 = 1     << 5
  bit4 = onOff << 4
  size = 12
  number = (2 ** size - 1) * percent / 100
  number = number << (12 - size)
  number = number << (12 - size)
  bottomPart = number % 256
  topPart = (number - bottomPart) >> 8
  firstByte = bit7 + bit6 + bit5 + bit4 + topPart
  secondByte = bottomPart
  return spi.xfer2([firstByte, secondByte])


def which_channel():
  channel = raw_input("Which channel do you want to test? Type 0 or 1.\n")
  while not channel.isdigit():
      channel = raw_input("Try again - just numbers 0 or 1 please!\n")
  return channel


def main():
  channel = 3
  while not (channel == 1 or channel == 0):
      channel = int(which_channel())
  
  print "These are the connections for the digital to analogue test:"
  print "Multimeter connections (set your meter to read V DC):"
  print "  connect black probe to GND"
  print "  connect red probe to DA%d on J29" % channel
  
  raw_input("When ready hit enter.\n")
  percent=[0,25,75,100]
  
  for p in percent:
      r = changeLevel(channel,1,p)
      print "Your meter should read about {0:.2f}V".format(p*2.048/100.0)
      raw_input("When ready hit enter.\n")

  r = changeLevel(0,0,0)
  r = changeLevel(1,0,0)

if __name__ == '__main__':
    main()
EOF
  chmod 755 ~pi/PiRT-Unit/dac_test.py
  chown pi ~pi/PiRT-Unit/dac_test.py
}

create_i2c_test()
{
  mkdir -p ~pi/PiRT-Unit/
  chown pi ~pi/PiRT-Unit/
  cat << EOF > ~pi/PiRT-Unit/i2c_test.py
#!/usr/bin/env python
# -*- coding: euc-jp -*- 
import smbus
import time

def main():

  # LCD initialize
  i2c = smbus.SMBus(1)
  addr = 0x3e
  contrast = 42   # 0-63
  i2c.write_byte_data(addr, 0, 0x38)  # function set(IS=0)
  i2c.write_byte_data(addr, 0, 0x39)  # function set(IS=1)
  i2c.write_byte_data(addr, 0, 0x14)  # internal osc
  i2c.write_byte_data(addr, 0,(0x70 | (contrast & 0x0f))) # contrast
  i2c.write_byte_data(addr, 0,(0x54 | ((contrast >> 4) & 0x03)))  # contrast/icon/power
  i2c.write_byte_data(addr, 0, 0x6c)  # follower control
  time.sleep(0.2)
  i2c.write_byte_data(addr, 0, 0x38)  # function set(IS=0)
  i2c.write_byte_data(addr, 0, 0x0C)  # Display On
  i2c.write_byte_data(addr, 0, 0x01)  # Clear Display
  i2c.write_byte_data(addr, 0, 0x06)  # Entry Mode Set
  time.sleep(0.2)

  # LCD Clear
  i2c.write_byte_data(addr, 0, 0x38)  # function set(IS=0)
  i2c.write_byte_data(addr, 0, 0x0C)  # Display On
  i2c.write_byte_data(addr, 0, 0x01)  # Clear Display
  i2c.write_byte_data(addr, 0, 0x06)  # Entry Mode Set
  time.sleep(0.2)


  # Send to LCD
  line1 = '__test__'
  for c in line1:
    i2c.write_byte_data(addr, 0x40, ord(c))
  i2c.write_byte_data(addr, 0, 0xc0)  # 2nd line
  line2 = '__!(^^)!__'
  for c in line2:
    i2c.write_byte_data(addr, 0x40, ord(c))



if __name__ == '__main__':
    main()

EOF
  chmod 755 ~pi/PiRT-Unit/i2c_test.py
  chown pi ~pi/PiRT-Unit/i2c_test.py
}

create_ministick()
{
  mkdir -p ~pi/PiRT-Unit/
  chown pi ~pi/PiRT-Unit/
  cat << EOF > ~pi/PiRT-Unit/Ministick.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-

"""
 @file Ministick.py
 @brief Phidget ministick sensor component
 @date $Date$

 @author 安藤慶昭

 LGPL

"""
import sys
import time
sys.path.append(".")

# Import RTM module
import RTC
import OpenRTM_aist

import math
import spidev

ministick_spec = ["implementation_id", "Ministick", 
		 "type_name",         "Ministick", 
		 "description",       "Phidget ministick sensor component", 
		 "version",           "1.0.0", 
		 "vendor",            "AIST", 
		 "category",          "Category", 
		 "activity_type",     "STATIC", 
		 "max_instance",      "1", 
		 "language",          "Python", 
		 "lang_type",         "SCRIPT",
		 "conf.default.scaling", "1.0",
		 "conf.default.tread", "0.2",
		 "conf.default.print_xy", "NO",
		 "conf.default.print_vel", "NO",
		 "conf.default.print_wvel", "NO",
		 "conf.__widget__.scaling", "slider.0.1",
		 "conf.__widget__.tread", "slider.0.01",
		 "conf.__widget__.print_xy", "radio",
		 "conf.__widget__.print_vel", "radio",
		 "conf.__widget__.print_wvel", "radio",
		 "conf.__constraints__.scaling", "0.0<=x<=10.0",
		 "conf.__constraints__.tread", "0.0<=x<=1.0",
		 "conf.__constraints__.print_xy", "(YES,NO)",
		 "conf.__constraints__.print_vel", "(YES,NO)",
		 "conf.__constraints__.print_wvel", "(YES,NO)",
		 ""]

##
# @class Ministick
# @brief Phidget ministick sensor component
#
# Phidget ministick sensor を PiRT-Unitに接続して利用するためのコンポーネント
#
# ・ジョイスティックの位置
# ・移動ロボットの速度ベクトル
# ・移動ロボットの車輪の角速度
#
#
class Ministick(OpenRTM_aist.DataFlowComponentBase):
	
	##
	# @brief constructor
	# @param manager Maneger Object
	#
	def __init__(self, manager):
		OpenRTM_aist.DataFlowComponentBase.__init__(self, manager)

		self._d_pos = RTC.TimedFloatSeq(RTC.Time(0,0),[])
		self._posOut = OpenRTM_aist.OutPort("pos", self._d_pos)
		self._d_vel = RTC.TimedVelocity2D(RTC.Time(0,0),0)
		self._velOut = OpenRTM_aist.OutPort("vel", self._d_vel)
		self._d_wheel_vel = RTC.TimedFloatSeq(RTC.Time(0,0),[])
		self._wheel_velOut = OpenRTM_aist.OutPort("wheel_vel", self._d_wheel_vel)
		self._scaling = [1.0]
		self._tread = [0.2]
		self._print_xy = ['NO']
		self._print_vel = ['NO']
		self._print_wvel = ['NO']
		self.x = 0.0
		self.y = 0.0
		self.spi = spidev.SpiDev()
		self.spi.open(0, 0)

	def get_adc(self, channel):
		sned_ch = [0x00,0x08,0x10,0x18]
		if ((channel > 3) or (channel < 0)):
			return -1
		r = self.spi.xfer2([sned_ch[channel],0,0,0])
		ret = ((r[2] << 6 ) & 0x300) |  ((r[2] << 6) & 0xc0) | ((r[3] >> 2) & 0x3f)
		return ret

	def xy_to_wvel(self, x, y):
		th = math.atan2(y, x)
		v = math.hypot(x, y)
		vl = v * math.cos(th - (math.pi/4.0))
		vr = v * math.sin(th - (math.pi/4.0))
		return (vl, vr)

	def wvel_to_vel2d(self, vl, vr):
		v = (vr + vl) / 2.0
		if v < 0.0:
			w = - (vr - vl) / self._tread[0]
		else:
			w = (vr - vl) / self._tread[0]
		return RTC.Velocity2D(v, 0.0, w)

	def onInitialize(self):
		# Bind variables and configuration variable
		self.bindParameter("scaling", self._scaling, "1.0")
		self.bindParameter("tread", self._tread, "0.2")
		self.bindParameter("print_xy", self._print_xy, "NO")
		self.bindParameter("print_vel", self._print_vel, "NO")
		self.bindParameter("print_wvel", self._print_wvel, "NO")
		
		self.addOutPort("pos",self._posOut)
		self.addOutPort("vel",self._velOut)
		self.addOutPort("wheel_vel",self._wheel_velOut)
		
		self.x_offset_v = 0.0
		self.y_offset_v = 0.0
		for i in range(1, 100):
			self.x_offset_v += self.get_adc(0)
			self.y_offset_v += self.get_adc(1)
		self.x_offset_v = self.x_offset_v / 100.0
		self.y_offset_v = self.y_offset_v / 100.0
		return RTC.RTC_OK
	
	def onFinalize(self, ec_id):
		return RTC.RTC_OK
	
	def onActivated(self, ec_id):
		return RTC.RTC_OK
	
	def onDeactivated(self, ec_id):
		return RTC.RTC_OK
	
	def onExecute(self, ec_id):
		self.x = - (self.get_adc(0) - self.x_offset_v) * self._scaling[0] / 1000.0
		self.y = (self.get_adc(1) - self.y_offset_v) * self._scaling[0] / 1000.0
		if self._print_xy[0] != "NO":
			print "(x, y) = ", self.x, self.y
		self._d_pos.data = [self.x, self.y]
		self._d_wheel_vel.data = self.xy_to_wvel(self.x, self.y)
		if self._print_wvel[0] != "NO":
			print "(vl, vr) = ", self._d_wheel_vel.data[0], self._d_wheel_vel.data[1]
		self._d_vel.data = self.wvel_to_vel2d(self._d_wheel_vel.data[0],
						      self._d_wheel_vel.data[1])
		if self._print_vel[0] != "NO":
			print "(vx, va) = ", self._d_vel.data.vx, self._d_vel.data.va
		self._posOut.write()
		self._velOut.write()
		self._wheel_velOut.write()
		return RTC.RTC_OK
	
def MinistickInit(manager):
    profile = OpenRTM_aist.Properties(defaults_str=ministick_spec)
    manager.registerFactory(profile,
                            Ministick,
                            OpenRTM_aist.Delete)

def MyModuleInit(manager):
    MinistickInit(manager)

    # Create a component
    comp = manager.createComponent("Ministick")

def main():
	mgr = OpenRTM_aist.Manager.init(sys.argv)
	mgr.setModuleInitProc(MyModuleInit)
	mgr.activateManager()
	mgr.runManager()

if __name__ == "__main__":
	main()

EOF
    chmod 755 ~pi/PiRT-Unit/Ministick.py
    chown pi ~pi/PiRT-Unit/Ministick.py
}

#============================================================
basic_setup()
{
  set_hostname
  install_packages
  setup_wpa_supplicant
  setup_network_if
  install_openrtm
  install_openrtm_python
}

kobuki_setup()
{
  create_kobuki_sh
  edit_rc_local
  install_kobuki
}

rtunit_setup()
{
  install_iodev_packages
  setup_raspi_blacklist
  create_udev_rules
  install_pyspidev
  install_wiringpi
  install_wiringpi_py

}

rtunit_examples()
{
  create_adc_test
  create_dac_test
  create_i2c_test
  create_ministick
}

#------------------------------
# main
#------------------------------
getopt $*

if test "x$TYPE" = "xbasic"; then
  basic_setup
fi

if test "x$TYPE" = "xkobuki"; then
  basic_setup
  kobuki_setup
fi

if test "x$TYPE" = "xkobuki_only"; then
  kobuki_setup
fi

if test "x$TYPE" = "xrtunit"; then
  basic_setup
  rtunit_setup
fi

if test "x$TYPE" = "xrtunit_only"; then
  rtunit_setup
fi

if test "x$TYPE" = "xrtunit_examples"; then
  rtunit_examples
fi
