import os
import re
def PatchFiles(source_dir):
    PatchLoacatedBit(source_dir)
    PatchConfigHeader(source_dir)


def PatchLoacatedBit(source_dir):
    file_path = os.path.join(source_dir, 'POUS.c')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 正则替换 __INIT_LOCATED(BOOL,__IX..,...) 为 __INIT_LOCATED_BOOL(BOOL,__IX..,bit,...)
    def replacer(match):
        ix = match.group(1)
        bit = match.group(2)
        var = match.group(3)
        var2 = match.group(4)
        return f'__INIT_LOCATED_BOOL(BOOL, {ix}, {int(bit)+1}, {var}, {var2})'
    # replacer = r'__INIT_LOCATED_BOOL(BOOL, \1, \2, \3, \4)'
    pattern = r'__INIT_LOCATED\(\s*BOOL,\s*(__\wX\d+_(\d+)),\s*([^,]+),\s*(\w+)\)'
    new_content = re.sub(pattern, replacer, content)
    # print(new_content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def PatchConfigHeader(source_dir):
    file_path = os.path.join(source_dir, 'Config0.h')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(config_header)

config_header=r'''

#ifndef __CONFIG_0_H
#define __CONFIG_0_H

#define __INIT_LOCATED_BOOL(type, location, bit, name, retained) \
    {                                                            \
        extern type *location;                                   \
        name.value = location;                                   \
        name.flags = (bit << 4);                                 \
        __INIT_RETAIN(name, retained)                            \
    }

#undef __INIT_LOCATED_VALUE
// not init bool located value to false automatically
#define __INIT_LOCATED_VALUE(name, initial) _Generic(name.value,                                     \
    BOOL *: ((initial && (name.flags & 0xf0)) && (*(name.value) |= (1 << ((name.flags >> 4) - 1)))), \
    default: *(name.value) = initial);

#undef __GET_LOCATED
// #define __GET_LOCATED(name, ...) _Generic((name.value),                                                                                                                                   \
//     BOOL *: (name.flags & __IEC_FORCE_FLAG) ? name.fvalue __VA_ARGS__ : ((name.flags & 0xf0) ? ((*(name.value))__VA_ARGS__) >> ((name.flags >> 4) - 1) & 1 : (*(name.value))__VA_ARGS__), \
//     default: ((name.flags & __IEC_FORCE_FLAG) ? name.fvalue __VA_ARGS__ : (*(name.value))__VA_ARGS__))

#define __GET_LOCATED(name, ...) _Generic((name.value),                                                                                                                                     \
    BOOL *: ((name.flags & __IEC_FORCE_FLAG) ? name.fvalue __VA_ARGS__ : ((name.flags & 0xf0) ? ((*(name.value))__VA_ARGS__) >> ((name.flags >> 4) - 1) & 1 : (*(name.value))__VA_ARGS__)), \
    default: ((name.flags & __IEC_FORCE_FLAG) ? name.fvalue __VA_ARGS__ : (*(name.value))__VA_ARGS__))

#undef __SET_LOCATED
#define __SET_LOCATED(prefix, name, suffix, new_value)                                                                                                                \
    if (!(prefix name.flags & __IEC_FORCE_FLAG))                                                                                                                      \
    {                                                                                                                                                                 \
        if (prefix name.flags & 0xf0)                                                                                                                                 \
        {                                                                                                                                                             \
            *(prefix name.value)suffix = (*(prefix name.value)suffix & ~(1 << ((prefix name.flags >> 4) - 1))) | ((new_value & 1) << ((prefix name.flags >> 4) - 1)); \
        }                                                                                                                                                             \
        else                                                                                                                                                          \
        {                                                                                                                                                             \
            *(prefix name.value)suffix = new_value;                                                                                                                   \
        }                                                                                                                                                             \
    }

#endif



'''