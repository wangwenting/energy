from setuptools import setup, Extension
from Cython.Distutils import build_ext


ext_names = (
    'airflow_mgr',
    'power_control',
    'outlettemp_mgr',
    'operation',
    'simplebalance_mgr',
    'senior_outlettemp_mgr',
    'scheduler_options',
)

cmdclass = {'build_ext': build_ext}
ext_modules = [
    Extension(
        ext,
        [ext + ".py"],
   )
   for ext in ext_names if ext.find('.') < 0]

ext_modules += [
    Extension(
        ext,
        ["/".join(ext.split('.')) + ".py"],
    )
    for ext in ext_names if ext.find('.') > 0]

setup(
    name='name',
    ext_modules=ext_modules,
    cmdclass=cmdclass,
)
