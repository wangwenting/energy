#           Copyright (c)  2015, Intel Corporation.
#
#   This Software is furnished under license and may only be used or
# copied in accordance with the terms of that license. No license,
# express or implied, by estoppel or otherwise, to any intellectual
# property rights is granted by this document. The Software is
# subject to change without notice, and should not be construed as
# a commitment by Intel Corporation to market, license, sell or
# support any product or technology. Unless otherwise provided for
# in the * license under which this Software is provided, the
# Software is provided AS IS, with no warranties of any kind,
# express or implied. Except as expressly permitted by the Software
# license, neither Intel Corporation nor its suppliers assumes any
# responsibility or liability for any errors or inaccuracies that
# may appear herein. Except as expressly permitted by the Software
# license, no part of the Software may be reproduced, stored in a
# retrieval system, transmitted in any form, or distributed by any
# means without the express written consent of Intel Corporation.
import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name="energy",
      version="0.0.1",
      author="wtwang",
      author_email="wentingx.wang@intel.com",
      description=("For distributed in Energy"),
      license="GPL",
      packages=find_packages(),
      long_description=read('README'),
      package_data={'': ['*.cfg','*.so']},
      data_files=[('/etc/energy', ['etc/energy/energy.conf']),
                  ('/etc/energy', ['etc/energy/energy-api.ini']),
                  ('/etc/energy', ['etc/energy/sensors.json']),
                  ('/etc/init', ['etc/init/energy-api.conf']),
                  ('/etc/init', ['etc/init/energy-sampler.conf']),
                  ('/etc/init', ['etc/init/energy-server.conf']),
                  ('/etc/init', ['etc/init/energy-agent.conf'])],

      classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: python2.7",
        "Framework :: Thrift Paste",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: Unix"],
      scripts=['energy/cmd/energy-api',
               'energy/cmd/energy-agent',
               'energy/cmd/energy-server',
               'energy/cmd/energy-sampler',
               'energy/cmd/energy-manager',
               'energy/cmd/schrestart'])
