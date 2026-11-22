#pragma once
#include "xbrz.h"

#ifdef BUILDING_DLL
#  define DLL_API __declspec(dllexport)
#else
#  define DLL_API __declspec(dllimport)
#endif

#ifdef __cplusplus
extern "C" {
#endif

	DLL_API void Scale(size_t factor, const uint32_t* src, uint32_t* trg,
		int srcWidth, int srcHeight, int colFmt, int yFirst, int yLast);

#ifdef __cplusplus
}
#endif