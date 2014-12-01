"""
 This module houses the OGR & SRS Exception objects, and the
 check_err() routine which checks the status code returned by
 OGR methods.
"""


#### OGR & SRS Exceptions ####
class GDALException(Exception):
    pass


class OGRException(Exception):
    pass


class SRSException(Exception):
    pass


class OGRIndexError(OGRException, KeyError):
    """
    This exception is raised when an invalid index is encountered, and has
    the 'silent_variable_feature' attribute set to true.  This ensures that
    django's templates proceed to use the next lookup type gracefully when
    an Exception is raised.  Fixes ticket #4740.
    """
    silent_variable_failure = True

#### OGR error checking codes and routine ####

# OGR Error Codes
OGRERR_DICT = {
    1: (OGRException, 'Not enough data.'),
    2: (OGRException, 'Not enough memory.'),
    3: (OGRException, 'Unsupported geometry type.'),
    4: (OGRException, 'Unsupported operation.'),
    5: (OGRException, 'Corrupt data.'),
    6: (OGRException, 'OGR failure.'),
    7: (SRSException, 'Unsupported SRS.'),
    8: (OGRException, 'Invalid handle.'),
}
OGRERR_NONE = 0

# CPL Error Codes
# http://www.gdal.org/cpl__error_8h.html
CPLERR_DICT = {
    1: (GDALException, 'AppDefined'),
    2: (GDALException, 'OutOfMemory'),
    3: (GDALException, 'FileIO'),
    4: (GDALException, 'OpenFailed'),
    5: (GDALException, 'IllegalArg'),
    6: (GDALException, 'NotSupported'),
    7: (GDALException, 'AssertionFailed'),
    8: (GDALException, 'NoWriteAccess'),
    9: (GDALException, 'UserInterrupt'),
    10: (GDALException, 'ObjectNull'),
}
CPLERR_NONE = 0


def check_err(code, cpl=False):
    """
    Checks the given CPL/OGRERR, and raises an exception where appropriate.
    """
    err_none = CPLERR_NONE if cpl else OGRERR_NONE
    err_dict = CPLERR_DICT if cpl else OGRERR_DICT

    if code == err_none:
        return
    elif code in err_dict:
        e, msg = err_dict[code]
        raise e(msg)
    else:
        raise GDALException('Unknown error code: "%s"' % code)
