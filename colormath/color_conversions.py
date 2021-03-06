"""
Conversion between color spaces.

.. note:: This module makes extensive use of imports within functions.
    That stinks.
"""

import math
import logging

import numpy

from colormath import color_constants
from colormath import spectral_constants
from colormath.color_objects import ColorBase
from colormath.chromatic_adaptation import apply_chromatic_adaptation
from colormath.color_exceptions import InvalidIlluminantError, UndefinedConversionError


logger = logging.getLogger(__name__)


# noinspection PyPep8Naming
def apply_RGB_matrix(var1, var2, var3, rgb_type, convtype="xyz_to_rgb"):
    """
    Applies an RGB working matrix to convert from XYZ to RGB.
    The arguments are tersely named var1, var2, and var3 to allow for the passing
    of XYZ _or_ RGB values. var1 is X for XYZ, and R for RGB. var2 and var3
    follow suite.
    """

    rgb_type = rgb_type.lower()
    convtype = convtype.lower()
    # Retrieve the appropriate transformation matrix from the constants.
    rgb_matrix = color_constants.RGB_SPECS[rgb_type]["conversions"][convtype]
   
    logger.debug("  \* Applying RGB conversion matrix: %s->%s", rgb_type, convtype)
    # Stuff the RGB/XYZ values into a NumPy matrix for conversion.
    var_matrix = numpy.array((
        var1, var2, var3
    ))
    # Perform the adaptation via matrix multiplication.
    result_matrix = numpy.dot(var_matrix, rgb_matrix)
    return result_matrix[0], result_matrix[1], result_matrix[2]


# noinspection PyPep8Naming,PyUnusedLocal
def Spectral_to_XYZ(cobj, illuminant_override=None, *args, **kwargs):
    """
    Converts spectral readings to XYZ.
    """

    from colormath.color_objects import XYZColor
    
    # If the user provides an illuminant_override numpy array, use it.
    if illuminant_override:
        reference_illum = illuminant_override
    else:
        # Otherwise, look up the illuminant from known standards based
        # on the value of 'illuminant' pulled from the SpectralColor object.
        try:
            reference_illum = spectral_constants.REF_ILLUM_TABLE[cobj.illuminant]
        except KeyError:
            raise InvalidIlluminantError(cobj.illuminant)
        
    # Get the spectral distribution of the selected standard observer.
    if cobj.observer == '10':
        std_obs_x = spectral_constants.STDOBSERV_X10
        std_obs_y = spectral_constants.STDOBSERV_Y10
        std_obs_z = spectral_constants.STDOBSERV_Z10
    else:
        # Assume 2 degree, since it is theoretically the only other possibility.
        std_obs_x = spectral_constants.STDOBSERV_X2
        std_obs_y = spectral_constants.STDOBSERV_Y2
        std_obs_z = spectral_constants.STDOBSERV_Z2
     
    # This is a NumPy array containing the spectral distribution of the color.
    sample = cobj.get_numpy_array()
    
    # The denominator is constant throughout the entire calculation for X,
    # Y, and Z coordinates. Calculate it once and re-use.
    denom = std_obs_y * reference_illum
    
    # This is also a common element in the calculation whereby the sample
    # NumPy array is multiplied by the reference illuminant's power distribution
    # (which is also a NumPy array).
    sample_by_ref_illum = sample * reference_illum
        
    # Calculate the numerator of the equation to find X.
    x_numerator = sample_by_ref_illum * std_obs_x
    y_numerator = sample_by_ref_illum * std_obs_y
    z_numerator = sample_by_ref_illum * std_obs_z
    
    xyz_x = x_numerator.sum() / denom.sum()
    xyz_y = y_numerator.sum() / denom.sum()
    xyz_z = z_numerator.sum() / denom.sum()
    
    return XYZColor(
        xyz_x, xyz_y, xyz_z, observer=cobj.observer, illuminant=cobj.illuminant)


# noinspection PyPep8Naming,PyUnusedLocal
def Lab_to_LCHab(cobj, *args, **kwargs):
    """
    Convert from CIE Lab to LCH(ab).
    """

    from colormath.color_objects import LCHabColor
   
    lch_l = cobj.lab_l
    lch_c = math.sqrt(math.pow(float(cobj.lab_a), 2) + math.pow(float(cobj.lab_b), 2))
    lch_h = math.atan2(float(cobj.lab_b), float(cobj.lab_a))
   
    if lch_h > 0:
        lch_h = (lch_h / math.pi) * 180
    else:
        lch_h = 360 - (math.fabs(lch_h) / math.pi) * 180
      
    return LCHabColor(
        lch_l, lch_c, lch_h, observer=cobj.observer, illuminant=cobj.illuminant)


# noinspection PyPep8Naming,PyUnusedLocal
def Lab_to_XYZ(cobj, *args, **kwargs):
    """
    Convert from Lab to XYZ
    """

    from colormath.color_objects import XYZColor

    illum = cobj.get_illuminant_xyz()
    xyz_y = (cobj.lab_l + 16.0) / 116.0
    xyz_x = cobj.lab_a / 500.0 + xyz_y
    xyz_z = xyz_y - cobj.lab_b / 200.0
   
    if math.pow(xyz_y, 3) > color_constants.CIE_E:
        xyz_y = math.pow(xyz_y, 3)
    else:
        xyz_y = (xyz_y - 16.0 / 116.0) / 7.787

    if math.pow(xyz_x, 3) > color_constants.CIE_E:
        xyz_x = math.pow(xyz_x, 3)
    else:
        xyz_x = (xyz_x - 16.0 / 116.0) / 7.787
      
    if math.pow(xyz_z, 3) > color_constants.CIE_E:
        xyz_z = math.pow(xyz_z, 3)
    else:
        xyz_z = (xyz_z - 16.0 / 116.0) / 7.787
      
    xyz_x = (illum["X"] * xyz_x)
    xyz_y = (illum["Y"] * xyz_y)
    xyz_z = (illum["Z"] * xyz_z)
    
    return XYZColor(
        xyz_x, xyz_y, xyz_z, observer=cobj.observer, illuminant=cobj.illuminant)


# noinspection PyPep8Naming,PyUnusedLocal
def Luv_to_LCHuv(cobj, *args, **kwargs):
    """
    Convert from CIE Luv to LCH(uv).
    """

    from colormath.color_objects import LCHuvColor
   
    lch_l = cobj.luv_l
    lch_c = math.sqrt(math.pow(cobj.luv_u, 2.0) + math.pow(cobj.luv_v, 2.0))
    lch_h = math.atan2(float(cobj.luv_v), float(cobj.luv_u))
   
    if lch_h > 0:
        lch_h = (lch_h / math.pi) * 180
    else:
        lch_h = 360 - (math.fabs(lch_h) / math.pi) * 180
    return LCHuvColor(
        lch_l, lch_c, lch_h, observer=cobj.observer, illuminant=cobj.illuminant)


# noinspection PyPep8Naming,PyUnusedLocal
def Luv_to_XYZ(cobj, *args, **kwargs):
    """
    Convert from Luv to XYZ.
    """

    from colormath.color_objects import XYZColor

    illum = cobj.get_illuminant_xyz()
    # Without Light, there is no color. Short-circuit this and avoid some
    # zero division errors in the var_a_frac calculation.
    if cobj.luv_l <= 0.0:
        xyz_x = 0.0
        xyz_y = 0.0
        xyz_z = 0.0
        return XYZColor(
            xyz_x, xyz_y, xyz_z, observer=cobj.observer, illuminant=cobj.illuminant)

    # Various variables used throughout the conversion.
    cie_k_times_e = color_constants.CIE_K * color_constants.CIE_E
    u_sub_0 = (4.0 * illum["X"]) / (illum["X"] + 15.0 * illum["Y"] + 3.0 * illum["Z"])
    v_sub_0 = (9.0 * illum["Y"]) / (illum["X"] + 15.0 * illum["Y"] + 3.0 * illum["Z"])
    var_u = cobj.luv_u / (13.0 * cobj.luv_l) + u_sub_0
    var_v = cobj.luv_v / (13.0 * cobj.luv_l) + v_sub_0

    # Y-coordinate calculations.
    if cobj.luv_l > cie_k_times_e:
        xyz_y = math.pow((cobj.luv_l + 16.0) / 116.0, 3.0)
    else:
        xyz_y = cobj.luv_l / color_constants.CIE_K

    # X-coordinate calculation.
    xyz_x = xyz_y * 9.0 * var_u / (4.0 * var_v)
    # Z-coordinate calculation.
    xyz_z = xyz_y * (12.0 - 3.0 * var_u - 20.0 * var_v) / (4.0 * var_v)

    return XYZColor(
        xyz_x, xyz_y, xyz_z, illuminant=cobj.illuminant, observer=cobj.observer)


# noinspection PyPep8Naming,PyUnusedLocal
def LCHab_to_Lab(cobj, *args, **kwargs):
    """
    Convert from LCH(ab) to Lab.
    """

    from colormath.color_objects import LabColor
   
    lab_l = cobj.lch_l
    lab_a = math.cos(math.radians(cobj.lch_h)) * cobj.lch_c
    lab_b = math.sin(math.radians(cobj.lch_h)) * cobj.lch_c
    return LabColor(
        lab_l, lab_a, lab_b, illuminant=cobj.illuminant, observer=cobj.observer)


# noinspection PyPep8Naming,PyUnusedLocal
def LCHuv_to_Luv(cobj, *args, **kwargs):
    """
    Convert from LCH(uv) to Luv.
    """

    from colormath.color_objects import LuvColor
   
    luv_l = cobj.lch_l
    luv_u = math.cos(math.radians(cobj.lch_h)) * cobj.lch_c
    luv_v = math.sin(math.radians(cobj.lch_h)) * cobj.lch_c
    return LuvColor(
        luv_l, luv_u, luv_v, illuminant=cobj.illuminant, observer=cobj.observer)


# noinspection PyPep8Naming,PyUnusedLocal
def xyY_to_XYZ(cobj, *args, **kwargs):
    """
    Convert from xyY to XYZ.
    """

    from colormath.color_objects import XYZColor
   
    xyz_x = (cobj.xyy_x * cobj.xyy_Y) / cobj.xyy_y
    xyz_y = cobj.xyy_Y
    xyz_z = ((1.0 - cobj.xyy_x - cobj.xyy_y) * xyz_y) / cobj.xyy_y
    
    return XYZColor(
        xyz_x, xyz_y, xyz_z, illuminant=cobj.illuminant, observer=cobj.observer)


# noinspection PyPep8Naming,PyUnusedLocal
def XYZ_to_xyY(cobj, *args, **kwargs):
    """
    Convert from XYZ to xyY.
    """

    from colormath.color_objects import xyYColor
   
    xyy_x = cobj.xyz_x / (cobj.xyz_x + cobj.xyz_y + cobj.xyz_z)
    xyy_y = cobj.xyz_y / (cobj.xyz_x + cobj.xyz_y + cobj.xyz_z)
    xyy_Y = cobj.xyz_y

    return xyYColor(
        xyy_x, xyy_y, xyy_Y, observer=cobj.observer, illuminant=cobj.illuminant)


# noinspection PyPep8Naming,PyUnusedLocal
def XYZ_to_Luv(cobj, *args, **kwargs):
    """
    Convert from XYZ to Luv
    """

    from colormath.color_objects import LuvColor
   
    temp_x = cobj.xyz_x
    temp_y = cobj.xyz_y
    temp_z = cobj.xyz_z
   
    luv_u = (4.0 * temp_x) / (temp_x + (15.0 * temp_y) + (3.0 * temp_z))
    luv_v = (9.0 * temp_y) / (temp_x + (15.0 * temp_y) + (3.0 * temp_z))

    illum = cobj.get_illuminant_xyz()
    temp_y = temp_y / illum["Y"]
    if temp_y > color_constants.CIE_E:
        temp_y = math.pow(temp_y, (1.0 / 3.0))
    else:
        temp_y = (7.787 * temp_y) + (16.0 / 116.0)
   
    ref_U = (4.0 * illum["X"]) / (illum["X"] + (15.0 * illum["Y"]) + (3.0 * illum["Z"]))
    ref_V = (9.0 * illum["Y"]) / (illum["X"] + (15.0 * illum["Y"]) + (3.0 * illum["Z"]))
   
    luv_l = (116.0 * temp_y) - 16.0
    luv_u = 13.0 * luv_l * (luv_u - ref_U)
    luv_v = 13.0 * luv_l * (luv_v - ref_V)
   
    return LuvColor(
        luv_l, luv_u, luv_v, observer=cobj.observer, illuminant=cobj.illuminant)


# noinspection PyPep8Naming,PyUnusedLocal
def XYZ_to_Lab(cobj, *args, **kwargs):
    """
    Converts XYZ to Lab.
    """

    from colormath.color_objects import LabColor

    illum = cobj.get_illuminant_xyz()
    temp_x = cobj.xyz_x / illum["X"]
    temp_y = cobj.xyz_y / illum["Y"]
    temp_z = cobj.xyz_z / illum["Z"]
   
    if temp_x > color_constants.CIE_E:
        temp_x = math.pow(temp_x, (1.0 / 3.0))
    else:
        temp_x = (7.787 * temp_x) + (16.0 / 116.0)     

    if temp_y > color_constants.CIE_E:
        temp_y = math.pow(temp_y, (1.0 / 3.0))
    else:
        temp_y = (7.787 * temp_y) + (16.0 / 116.0)
   
    if temp_z > color_constants.CIE_E:
        temp_z = math.pow(temp_z, (1.0 / 3.0))
    else:
        temp_z = (7.787 * temp_z) + (16.0 / 116.0)
      
    lab_l = (116.0 * temp_y) - 16.0
    lab_a = 500.0 * (temp_x - temp_y)
    lab_b = 200.0 * (temp_y - temp_z)
    return LabColor(
        lab_l, lab_a, lab_b, observer=cobj.observer, illuminant=cobj.illuminant)


# noinspection PyPep8Naming,PyUnusedLocal
def XYZ_to_RGB(cobj, target_rgb="srgb", *args, **kwargs):
    """
    XYZ to RGB conversion.
    """

    from colormath.color_objects import RGBColor
    target_rgb = target_rgb.lower()

    temp_X = cobj.xyz_x
    temp_Y = cobj.xyz_y
    temp_Z = cobj.xyz_z

    logger.debug("  \- Target RGB space: %s", target_rgb)
    target_illum = color_constants.RGB_SPECS[target_rgb]["native_illum"]
    logger.debug("  \- Target native illuminant: %s", target_illum)
    logger.debug("  \- XYZ color's illuminant: %s", cobj.illuminant)
   
    # If the XYZ values were taken with a different reference white than the
    # native reference white of the target RGB space, a transformation matrix
    # must be applied.
    if cobj.illuminant != target_illum:
        logger.debug("  \* Applying transformation from %s to %s ",
                     cobj.illuminant, target_illum)
        # Get the adjusted XYZ values, adapted for the target illuminant.
        temp_X, temp_Y, temp_Z = apply_chromatic_adaptation(
            temp_X, temp_Y, temp_Z,
            orig_illum=cobj.illuminant, targ_illum=target_illum)
        logger.debug("  \*   New values: %.3f, %.3f, %.3f",
                     temp_X, temp_Y, temp_Z)
   
    # Apply an RGB working space matrix to the XYZ values (matrix mul).
    rgb_r, rgb_g, rgb_b = apply_RGB_matrix(
        temp_X, temp_Y, temp_Z,
        rgb_type=target_rgb, convtype="xyz_to_rgb")

    # v
    linear_channels = dict(r=rgb_r, g=rgb_g, b=rgb_b)
    # V
    nonlinear_channels = {}
    if target_rgb == "srgb":
        for channel in ['r', 'g', 'b']:
            v = linear_channels[channel]
            if v <= 0.0031308:
                nonlinear_channels[channel] = v * 12.92
            else:
                nonlinear_channels[channel] = 1.055 * math.pow(v, 1 / 2.4) - 0.055
    else:
        # If it's not sRGB...
        gamma = color_constants.RGB_SPECS[target_rgb]["gamma"]

        for channel in ['r', 'g', 'b']:
            v = linear_channels[channel]
            nonlinear_channels[channel] = v * 12.92

    return RGBColor(
        nonlinear_channels['r'], nonlinear_channels['g'], nonlinear_channels['b'],
        rgb_type=target_rgb)


# noinspection PyPep8Naming,PyUnusedLocal
def RGB_to_XYZ(cobj, target_illuminant=None, *args, **kwargs):
    """
    RGB to XYZ conversion. Expects 0-255 RGB values.

    Based off of: http://www.brucelindbloom.com/index.html?Eqn_RGB_to_XYZ.html
    """

    from colormath.color_objects import XYZColor

    # Will contain linearized RGB channels (removed the gamma func).
    linear_channels = {}

    if cobj.rgb_type == "srgb":
        for channel in ['r', 'g', 'b']:
            V = getattr(cobj, 'rgb_' + channel)
            if V <= 0.04045:
                linear_channels[channel] = V / 12.92
            else:
                linear_channels[channel] = math.pow((V + 0.055) / 1.055, 2.4)
    else:
        # If it's not sRGB...
        gamma = color_constants.RGB_SPECS[cobj.rgb_type]["gamma"]

        for channel in ['r', 'g', 'b']:
            V = getattr(cobj, 'rgb_' + channel)
            linear_channels[channel] = math.pow(V, gamma)
        
    # Apply an RGB working space matrix to the XYZ values (matrix mul).
    xyz_x, xyz_y, xyz_z = apply_RGB_matrix(
        linear_channels['r'], linear_channels['g'], linear_channels['b'],
        rgb_type=cobj.rgb_type, convtype="rgb_to_xyz")

    if target_illuminant is None:
        target_illuminant = color_constants.RGB_SPECS[cobj.rgb_type]["native_illum"]
    
    # The illuminant of the original RGB object. This will always match
    # the RGB colorspace's native illuminant.
    illuminant = color_constants.RGB_SPECS[cobj.rgb_type]["native_illum"]
    xyzcolor = XYZColor(xyz_x, xyz_y, xyz_z, illuminant=illuminant)
    # This will take care of any illuminant changes for us (if source
    # illuminant != target illuminant).
    xyzcolor.apply_adaptation(target_illuminant)

    return xyzcolor


# noinspection PyPep8Naming,PyUnusedLocal
def __RGB_to_Hue(var_R, var_G, var_B, var_min, var_max):
    """
    For RGB_to_HSL and RGB_to_HSV, the Hue (H) component is calculated in
    the same way.
    """

    if var_max == var_min:
        return 0.0
    elif var_max == var_R:
        return (60.0 * ((var_G - var_B) / (var_max - var_min)) + 360) % 360.0
    elif var_max == var_G:
        return 60.0 * ((var_B - var_R) / (var_max - var_min)) + 120
    elif var_max == var_B:
        return 60.0 * ((var_R - var_G) / (var_max - var_min)) + 240.0


# noinspection PyPep8Naming,PyUnusedLocal
def RGB_to_HSV(cobj, *args, **kwargs):
    """
    Converts from RGB to HSV.
    
    H values are in degrees and are 0 to 360.
    S values are a percentage, 0.0 to 1.0.
    V values are a percentage, 0.0 to 1.0.
    """

    from colormath.color_objects import HSVColor
    
    var_R = cobj.rgb_r
    var_G = cobj.rgb_g
    var_B = cobj.rgb_b
    
    var_max = max(var_R, var_G, var_B)
    var_min = min(var_R, var_G, var_B)
    
    var_H = __RGB_to_Hue(var_R, var_G, var_B, var_min, var_max)
    
    if var_max == 0:
        var_S = 0
    else:
        var_S = 1.0 - (var_min / var_max)
        
    var_V = var_max

    hsv_h = var_H
    hsv_s = var_S
    hsv_v = var_V

    return HSVColor(
        var_H, var_S, var_V, rgb_type=cobj.rgb_type)


# noinspection PyPep8Naming,PyUnusedLocal
def RGB_to_HSL(cobj, *args, **kwargs):
    """
    Converts from RGB to HSL.
    
    H values are in degrees and are 0 to 360.
    S values are a percentage, 0.0 to 1.0.
    L values are a percentage, 0.0 to 1.0.
    """

    from colormath.color_objects import HSLColor
    
    var_R = cobj.rgb_r
    var_G = cobj.rgb_g
    var_B = cobj.rgb_b
    
    var_max = max(var_R, var_G, var_B)
    var_min = min(var_R, var_G, var_B)
    
    var_H = __RGB_to_Hue(var_R, var_G, var_B, var_min, var_max)
    var_L = 0.5 * (var_max + var_min)
    
    if var_max == var_min:
        var_S = 0
    elif var_L <= 0.5:
        var_S = (var_max - var_min) / (2.0 * var_L)
    else:
        var_S = (var_max - var_min) / (2.0 - (2.0 * var_L))
    
    return HSLColor(
        var_H, var_S, var_L, rgb_type=cobj.rgb_type)


# noinspection PyPep8Naming,PyUnusedLocal
def __Calc_HSL_to_RGB_Components(var_q, var_p, C):
    """
    This is used in HSL_to_RGB conversions on R, G, and B.
    """

    if C < 0:
        C += 1.0
    if C > 1:
        C -= 1.0

    # Computing C of vector (Color R, Color G, Color B)
    if C < (1.0 / 6.0):
        return var_p + ((var_q - var_p) * 6.0 * C)
    elif (1.0 / 6.0) <= C < 0.5:
        return var_q
    elif 0.5 <= C < (2.0 / 3.0):
        return var_p + ((var_q - var_p) * 6.0 * ((2.0 / 3.0) - C))
    else:
        return var_p


# noinspection PyPep8Naming,PyUnusedLocal
def HSV_to_RGB(cobj, target_rgb=None, *args, **kwargs):
    """
    HSV to RGB conversion.
    
    H values are in degrees and are 0 to 360.
    S values are a percentage, 0.0 to 1.0.
    V values are a percentage, 0.0 to 1.0.
    """

    from colormath.color_objects import RGBColor
    
    H = cobj.hsv_h
    S = cobj.hsv_s
    V = cobj.hsv_v
    
    h_floored = int(math.floor(H))
    h_sub_i = int(h_floored / 60) % 6
    var_f = (H / 60.0) - (h_floored // 60)
    var_p = V * (1.0 - S)
    var_q = V * (1.0 - var_f * S)
    var_t = V * (1.0 - (1.0 - var_f) * S)
       
    if h_sub_i == 0:
        rgb_r = V
        rgb_g = var_t
        rgb_b = var_p
    elif h_sub_i == 1:
        rgb_r = var_q
        rgb_g = V
        rgb_b = var_p
    elif h_sub_i == 2:
        rgb_r = var_p
        rgb_g = V
        rgb_b = var_t
    elif h_sub_i == 3:
        rgb_r = var_p
        rgb_g = var_q
        rgb_b = V
    elif h_sub_i == 4:
        rgb_r = var_t
        rgb_g = var_p
        rgb_b = V
    elif h_sub_i == 5:
        rgb_r = V
        rgb_g = var_p
        rgb_b = var_q
    else:
        raise ValueError("Unable to convert HSL->RGB due to value error.")

    # In the event that they define an HSV color and want to convert it to 
    # a particular RGB space, let them override it here.
    if target_rgb is not None:
        rgb_type = target_rgb
    else:
        rgb_type = cobj.rgb_type
        
    return RGBColor(rgb_r, rgb_g, rgb_b, rgb_type=rgb_type)


# noinspection PyPep8Naming,PyUnusedLocal
def HSL_to_RGB(cobj, target_rgb=None, *args, **kwargs):
    """
    HSL to RGB conversion.
    """

    from colormath.color_objects import RGBColor
    
    H = cobj.hsl_h
    S = cobj.hsl_s
    L = cobj.hsl_l
    
    if L < 0.5:
        var_q = L * (1.0 + S)
    else:
        var_q = L + S - (L * S)
        
    var_p = 2.0 * L - var_q
    
    # H normalized to range [0,1]
    h_sub_k = (H / 360.0)
    
    t_sub_R = h_sub_k + (1.0 / 3.0)
    t_sub_G = h_sub_k
    t_sub_B = h_sub_k - (1.0 / 3.0)
    
    rgb_r = __Calc_HSL_to_RGB_Components(var_q, var_p, t_sub_R)
    rgb_g = __Calc_HSL_to_RGB_Components(var_q, var_p, t_sub_G)
    rgb_b = __Calc_HSL_to_RGB_Components(var_q, var_p, t_sub_B)

    # In the event that they define an HSV color and want to convert it to 
    # a particular RGB space, let them override it here.
    if target_rgb is not None:
        rgb_type = target_rgb
    else:
        rgb_type = cobj.rgb_type
    
    return RGBColor(rgb_r, rgb_g, rgb_b, rgb_type=rgb_type)


# noinspection PyPep8Naming,PyUnusedLocal
def RGB_to_CMY(cobj, *args, **kwargs):
    """
    RGB to CMY conversion.
    
    NOTE: CMYK and CMY values range from 0.0 to 1.0
    """

    from colormath.color_objects import CMYColor
   
    cmy_c = 1.0 - cobj.rgb_r
    cmy_m = 1.0 - cobj.rgb_g
    cmy_y = 1.0 - cobj.rgb_b
    
    return CMYColor(cmy_c, cmy_m, cmy_y)


# noinspection PyPep8Naming,PyUnusedLocal
def CMY_to_RGB(cobj, *args, **kwargs):
    """
    Converts CMY to RGB via simple subtraction.
    
    NOTE: Returned values are in the range of 0-255.
    """

    from colormath.color_objects import RGBColor
    
    rgb_r = 1.0 - cobj.cmy_c
    rgb_g = 1.0 - cobj.cmy_m
    rgb_b = 1.0 - cobj.cmy_y
    
    return RGBColor(rgb_r, rgb_g, rgb_b)


# noinspection PyPep8Naming,PyUnusedLocal
def CMY_to_CMYK(cobj, *args, **kwargs):
    """
    Converts from CMY to CMYK.
    
    NOTE: CMYK and CMY values range from 0.0 to 1.0
    """

    from colormath.color_objects import CMYKColor
   
    var_k = 1.0
    if cobj.cmy_c < var_k:
        var_k = cobj.cmy_c
    if cobj.cmy_m < var_k:
        var_k = cobj.cmy_m
    if cobj.cmy_y < var_k:
        var_k = cobj.cmy_y
      
    if var_k == 1:
        cmyk_c = 0.0
        cmyk_m = 0.0
        cmyk_y = 0.0
    else:
        cmyk_c = (cobj.cmy_c - var_k) / (1.0 - var_k)
        cmyk_m = (cobj.cmy_m - var_k) / (1.0 - var_k)
        cmyk_y = (cobj.cmy_y - var_k) / (1.0 - var_k)
    cmyk_k = var_k

    return CMYKColor(cmyk_c, cmyk_m, cmyk_y, cmyk_k)


# noinspection PyPep8Naming,PyUnusedLocal
def CMYK_to_CMY(cobj, *args, **kwargs):
    """
    Converts CMYK to CMY.
    
    NOTE: CMYK and CMY values range from 0.0 to 1.0
    """

    from colormath.color_objects import CMYColor
    
    cmy_c = cobj.cmyk_c * (1.0 - cobj.cmyk_k) + cobj.cmyk_k
    cmy_m = cobj.cmyk_m * (1.0 - cobj.cmyk_k) + cobj.cmyk_k
    cmy_y = cobj.cmyk_y * (1.0 - cobj.cmyk_k) + cobj.cmyk_k
    
    return CMYColor(cmy_c, cmy_m, cmy_y)


CONVERSION_TABLE = {
    "SpectralColor": {
        "SpectralColor": [None],
        "XYZColor": [Spectral_to_XYZ],
        "xyYColor": [Spectral_to_XYZ, XYZ_to_xyY],
        "LabColor": [Spectral_to_XYZ, XYZ_to_Lab],
        "LCHColor": [Spectral_to_XYZ, XYZ_to_Lab, Lab_to_LCHab],
        "LuvColor": [Spectral_to_XYZ, XYZ_to_Luv],
        "RGBColor": [Spectral_to_XYZ, XYZ_to_RGB],
        "HSLColor": [Spectral_to_XYZ, XYZ_to_RGB, RGB_to_HSL],
        "HSVColor": [Spectral_to_XYZ, XYZ_to_RGB, RGB_to_HSV],
        "CMYColor": [Spectral_to_XYZ, XYZ_to_RGB, RGB_to_CMY],
       "CMYKColor": [Spectral_to_XYZ, XYZ_to_RGB, RGB_to_CMY, CMY_to_CMYK],
    },
    "LabColor": {
        "LabColor": [None],
        "XYZColor": [Lab_to_XYZ],
        "xyYColor": [Lab_to_XYZ, XYZ_to_xyY],
      "LCHabColor": [Lab_to_LCHab],
      "LCHuvColor": [Lab_to_XYZ, XYZ_to_Luv, Luv_to_LCHuv],
        "LuvColor": [Lab_to_XYZ, XYZ_to_Luv],
        "RGBColor": [Lab_to_XYZ, XYZ_to_RGB],
        "HSLColor": [Lab_to_XYZ, XYZ_to_RGB, RGB_to_HSL],
        "HSVColor": [Lab_to_XYZ, XYZ_to_RGB, RGB_to_HSV],
        "CMYColor": [Lab_to_XYZ, XYZ_to_RGB, RGB_to_CMY],
       "CMYKColor": [Lab_to_XYZ, XYZ_to_RGB, RGB_to_CMY, CMY_to_CMYK],
    },
    "LCHabColor": {
      "LCHabColor": [None],
        "XYZColor": [LCHab_to_Lab, Lab_to_XYZ],
        "xyYColor": [LCHab_to_Lab, Lab_to_XYZ, XYZ_to_xyY],
        "LabColor": [LCHab_to_Lab],
      "LCHuvColor": [LCHab_to_Lab, Lab_to_XYZ, XYZ_to_Luv, Luv_to_LCHuv],
        "LuvColor": [LCHab_to_Lab, Lab_to_XYZ, XYZ_to_Luv],
        "RGBColor": [LCHab_to_Lab, Lab_to_XYZ, XYZ_to_RGB],
        "HSLColor": [LCHab_to_Lab, Lab_to_XYZ, XYZ_to_RGB, RGB_to_HSL],
        "HSVColor": [LCHab_to_Lab, Lab_to_XYZ, XYZ_to_RGB, RGB_to_HSV],
        "CMYColor": [LCHab_to_Lab, Lab_to_XYZ, XYZ_to_RGB, RGB_to_CMY],
       "CMYKColor": [LCHab_to_Lab, Lab_to_XYZ, XYZ_to_RGB, RGB_to_CMY, CMY_to_CMYK],
    },
    "LCHuvColor": {
      "LCHuvColor": [None],
        "XYZColor": [LCHuv_to_Luv, Luv_to_XYZ],
        "xyYColor": [LCHuv_to_Luv, Luv_to_XYZ, XYZ_to_xyY],
        "LabColor": [LCHuv_to_Luv, Luv_to_XYZ, XYZ_to_Lab],
        "LuvColor": [LCHuv_to_Luv],
      "LCHabColor": [LCHuv_to_Luv, Luv_to_XYZ, XYZ_to_Lab, Lab_to_LCHab],
        "RGBColor": [LCHuv_to_Luv, Luv_to_XYZ, XYZ_to_RGB],
        "HSLColor": [LCHuv_to_Luv, Luv_to_XYZ, XYZ_to_RGB, RGB_to_HSL],
        "HSVColor": [LCHuv_to_Luv, Luv_to_XYZ, XYZ_to_RGB, RGB_to_HSV],
        "CMYColor": [LCHuv_to_Luv, Luv_to_XYZ, XYZ_to_RGB, RGB_to_CMY],
       "CMYKColor": [LCHuv_to_Luv, Luv_to_XYZ, XYZ_to_RGB, RGB_to_CMY, CMY_to_CMYK],
    },
    "LuvColor": {
        "LuvColor": [None],
        "XYZColor": [Luv_to_XYZ],
        "xyYColor": [Luv_to_XYZ, XYZ_to_xyY],
        "LabColor": [Luv_to_XYZ, XYZ_to_Lab],
      "LCHabColor": [Luv_to_XYZ, XYZ_to_Lab, Lab_to_LCHab],
      "LCHuvColor": [Luv_to_LCHuv],
        "RGBColor": [Luv_to_XYZ, XYZ_to_RGB],
        "HSLColor": [Luv_to_XYZ, XYZ_to_RGB, RGB_to_HSL],
        "HSVColor": [Luv_to_XYZ, XYZ_to_RGB, RGB_to_HSV],
        "CMYColor": [Luv_to_XYZ, XYZ_to_RGB, RGB_to_CMY],
       "CMYKColor": [Luv_to_XYZ, XYZ_to_RGB, RGB_to_CMY, CMY_to_CMYK],
    },
    "XYZColor": {
        "XYZColor": [None],
        "xyYColor": [XYZ_to_xyY],
        "LabColor": [XYZ_to_Lab],
      "LCHabColor": [XYZ_to_Lab, Lab_to_LCHab],
      "LCHuvColor": [XYZ_to_Lab, Luv_to_LCHuv],
        "LuvColor": [XYZ_to_Luv],
        "RGBColor": [XYZ_to_RGB],
        "HSLColor": [XYZ_to_RGB, RGB_to_HSL],
        "HSVColor": [XYZ_to_RGB, RGB_to_HSV],
        "CMYColor": [XYZ_to_RGB, RGB_to_CMY],
       "CMYKColor": [XYZ_to_RGB, RGB_to_CMY, CMY_to_CMYK],
    },
    "xyYColor": {
        "xyYColor": [None],
        "XYZColor": [xyY_to_XYZ],
        "LabColor": [xyY_to_XYZ, XYZ_to_Lab],
      "LCHabColor": [xyY_to_XYZ, XYZ_to_Lab, Lab_to_LCHab],
      "LCHuvColor": [xyY_to_XYZ, XYZ_to_Luv, Luv_to_LCHuv],
        "LuvColor": [xyY_to_XYZ, XYZ_to_Luv],
        "RGBColor": [xyY_to_XYZ, XYZ_to_RGB],
        "HSLColor": [xyY_to_XYZ, XYZ_to_RGB, RGB_to_HSL],
        "HSVColor": [xyY_to_XYZ, XYZ_to_RGB, RGB_to_HSV],
        "CMYColor": [xyY_to_XYZ, XYZ_to_RGB, RGB_to_CMY],
       "CMYKColor": [xyY_to_XYZ, XYZ_to_RGB, RGB_to_CMY, CMY_to_CMYK],
    },
    "RGBColor": {
        "RGBColor": [None],
        "HSLColor": [RGB_to_HSL],
        "HSVColor": [RGB_to_HSV],
        "CMYColor": [RGB_to_CMY],
       "CMYKColor": [RGB_to_CMY, CMY_to_CMYK],
        "XYZColor": [RGB_to_XYZ],
        "xyYColor": [RGB_to_XYZ, XYZ_to_xyY],
        "LabColor": [RGB_to_XYZ, XYZ_to_Lab],
      "LCHabColor": [RGB_to_XYZ, XYZ_to_Lab, Lab_to_LCHab],
      "LCHuvColor": [RGB_to_XYZ, XYZ_to_Luv, Luv_to_LCHuv],
        "LuvColor": [RGB_to_XYZ, XYZ_to_Luv],
    },
    "HSLColor": {
        "HSLColor": [None],
        "HSVColor": [HSL_to_RGB, RGB_to_HSV],
        "RGBColor": [HSL_to_RGB],
        "CMYColor": [HSL_to_RGB, RGB_to_CMY],
       "CMYKColor": [HSL_to_RGB, RGB_to_CMY, CMY_to_CMYK],
        "XYZColor": [HSL_to_RGB, RGB_to_XYZ],
        "xyYColor": [HSL_to_RGB, RGB_to_XYZ, XYZ_to_xyY],
        "LabColor": [HSL_to_RGB, RGB_to_XYZ, XYZ_to_Lab],
      "LCHabColor": [HSL_to_RGB, RGB_to_XYZ, XYZ_to_Lab, Lab_to_LCHab],
      "LCHuvColor": [HSL_to_RGB, RGB_to_XYZ, XYZ_to_Luv, Luv_to_LCHuv],
        "LuvColor": [HSL_to_RGB, RGB_to_XYZ, XYZ_to_RGB],
    },
    "HSVColor": {
        "HSVColor": [None],
        "HSLColor": [HSV_to_RGB, RGB_to_HSL],
        "RGBColor": [HSV_to_RGB],
        "CMYColor": [HSV_to_RGB, RGB_to_CMY],
       "CMYKColor": [HSV_to_RGB, RGB_to_CMY, CMY_to_CMYK],
        "XYZColor": [HSV_to_RGB, RGB_to_XYZ],
        "xyYColor": [HSV_to_RGB, RGB_to_XYZ, XYZ_to_xyY],
        "LabColor": [HSV_to_RGB, RGB_to_XYZ, XYZ_to_Lab],
      "LCHabColor": [HSV_to_RGB, RGB_to_XYZ, XYZ_to_Lab, Lab_to_LCHab],
      "LCHuvColor": [HSV_to_RGB, RGB_to_XYZ, XYZ_to_Luv, Luv_to_LCHuv],
        "LuvColor": [HSV_to_RGB, RGB_to_XYZ, XYZ_to_RGB],
    },
    "CMYColor": {
        "CMYColor": [None],
       "CMYKColor": [CMY_to_CMYK],
        "HSLColor": [CMY_to_RGB, RGB_to_HSL],
        "HSVColor": [CMY_to_RGB, RGB_to_HSV],
        "RGBColor": [CMY_to_RGB],
        "XYZColor": [CMY_to_RGB, RGB_to_XYZ],
        "xyYColor": [CMY_to_RGB, RGB_to_XYZ, XYZ_to_xyY],
        "LabColor": [CMY_to_RGB, RGB_to_XYZ, XYZ_to_Lab],
      "LCHabColor": [CMY_to_RGB, RGB_to_XYZ, XYZ_to_Lab, Lab_to_LCHab],
      "LCHuvColor": [CMY_to_RGB, RGB_to_XYZ, XYZ_to_Luv, Luv_to_LCHuv],
        "LuvColor": [CMY_to_RGB, RGB_to_XYZ, XYZ_to_RGB],
    },
    "CMYKColor": {
       "CMYKColor": [None],
        "CMYColor": [CMYK_to_CMY],
        "HSLColor": [CMYK_to_CMY, CMY_to_RGB, RGB_to_HSL],
        "HSVColor": [CMYK_to_CMY, CMY_to_RGB, RGB_to_HSV],
        "RGBColor": [CMYK_to_CMY, CMY_to_RGB],
        "XYZColor": [CMYK_to_CMY, CMY_to_RGB, RGB_to_XYZ],
        "xyYColor": [CMYK_to_CMY, CMY_to_RGB, RGB_to_XYZ, XYZ_to_xyY],
        "LabColor": [CMYK_to_CMY, CMY_to_RGB, RGB_to_XYZ, XYZ_to_Lab],
      "LCHabColor": [CMYK_to_CMY, CMY_to_RGB, RGB_to_XYZ, XYZ_to_Lab, Lab_to_LCHab],
      "LCHuvColor": [CMYK_to_CMY, CMY_to_RGB, RGB_to_XYZ, XYZ_to_Luv, Luv_to_LCHuv],
        "LuvColor": [CMYK_to_CMY, CMY_to_RGB, RGB_to_XYZ, XYZ_to_RGB],
    }
}


def convert_color(color, target_cs, *args, **kwargs):
    """
    Converts the color to the designated color space.

    :param color: A Color instance to convert.
    :param target_cs: The Color class to convert to. Note that this is not
        an instance, but a class.
    :returns: An instance of the type passed in as ``target_cs``.
    :raises: :py:exc:`colormath.color_exceptions.UndefinedConversionError`
        if conversion between the two color spaces isn't possible.
    """

    if isinstance(target_cs, str):
        raise ValueError("target_cs parameter must be a Color object.")
    if not issubclass(target_cs, ColorBase):
        raise ValueError("target_cs parameter must be a Color object.")

    # Find the origin color space's conversion table.
    cs_table = CONVERSION_TABLE[color.__class__.__name__]
    try:
        # Look up the conversion path for the specified color space.
        conversions = cs_table[target_cs.__name__]
    except KeyError:
        raise UndefinedConversionError(
            color.__class__.__name__,
            target_cs.__name__,
        )

    logger.debug('Converting %s to %s', color, target_cs)
    logger.debug(' @ Conversion path: %s', conversions)

    # Start with original color in case we convert to the same color space.
    new_color = color
    # Iterate through the list of functions for the conversion path, storing
    # the results in a dictionary via update(). This way the user has access
    # to all of the variables involved in the conversion.
    for func in conversions:
        # Execute the function in this conversion step and store the resulting
        # Color object.
        logger.debug(' * Conversion: %s passed to %s()',
                     new_color.__class__.__name__, func)
        logger.debug(' |->  in %s', new_color)

        if func:
            # This can be None if you try to convert a color to the color
            # space that is already in. IE: XYZ->XYZ.
            new_color = func(new_color, *args, **kwargs)

        logger.debug(' |-< out %s', new_color)
    return new_color
