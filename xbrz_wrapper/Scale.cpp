#include "Scale.h"

extern "C" DLL_API void Scale(size_t factor, const uint32_t* src, uint32_t* trg, int srcWidth, int srcHeight, int colFmt, int yFirst, int yLast)
{
	const xbrz::ScalerCfg cfg = xbrz::ScalerCfg();
	xbrz::ColorFormat color = static_cast<xbrz::ColorFormat>(colFmt);
	return xbrz::scale(factor, src, trg, srcWidth, srcHeight, color, cfg, yFirst, yLast);
}
