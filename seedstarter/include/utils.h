#ifndef UTILS_H
#define UTILS_H

#include <3ds.h>

#define touchInRect(x1, x2, y1, y2) ((touchGetX() >= (x1) && touchGetX() <= (x2)) && (touchGetY() >= (y1) && touchGetY() <= (y2)))

bool isN3DS(void);
void u16_to_u8(char * buf, u16 * input, size_t bufsize);
u16 touchGetX(void);
u16 touchGetY(void);

#endif