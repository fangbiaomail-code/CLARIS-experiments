/* Functional equality of scalar and four-lane namespace hashing. */
#include <stdio.h>
#include <string.h>
#include "hash.h"

int main(void) {
    uint8_t input[4][67], scalar[4][32], vector[4][32], digest[32];
    for (int lane=0; lane<4; ++lane)
        for (int j=0; j<67; ++j) input[lane][j]=(uint8_t)(j+37*lane);
    for (uint8_t stage=1; stage<=9; ++stage) {
        hash_state_x4 x;
        claris_proof_hash_init_x4(&x, stage);
        hash_update_x4_4(&x,input[0],input[1],input[2],input[3],67);
        hash_final_x4_4(&x,vector[0],vector[1],vector[2],vector[3],32);
        for (int lane=0; lane<4; ++lane) {
            hash_state h;
            claris_proof_hash_init(&h, stage);
            hash_update(&h,input[lane],67);
            hash_final(&h,scalar[lane],32);
            if (memcmp(scalar[lane],vector[lane],32)) return 1;
        }
        printf("stage_%u ",stage);
        for(int j=0;j<32;++j)printf("%02x",scalar[0][j]);
        putchar('\n');
    }
    hash_state h;
    hash_init(&h); hash_update(&h,"public-wrapper-probe",20); hash_final(&h,digest,32);
    printf("wrapper ");for(int j=0;j<32;++j)printf("%02x",digest[j]);putchar('\n');
    puts("SCALAR_X4_PASS");
    return 0;
}
