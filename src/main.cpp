#include <Arduino.h>
#include <driver/i2s.h>

#define I2S_WS   25
#define I2S_SCK  26
#define I2S_SD   39
#define I2S_PORT I2S_NUM_0

#define SAMPLE_RATE  16000   
#define BUFFER_LEN   256
#define SERIAL_BAUD  460800  // Safe Mac baud rate

#define SAMPLE_SHIFT 14

int32_t samples[BUFFER_LEN];
uint8_t ulawBuf[BUFFER_LEN]; // Buffer to hold our compressed 8-bit data

// --- The G.711 mu-law Compression Algorithm ---
uint8_t encode_ulaw(int16_t pcm_val) {
    int sign = (pcm_val < 0) ? 0x80 : 0x00;
    if (pcm_val < 0) pcm_val = -pcm_val;
    if (pcm_val > 32635) pcm_val = 32635;
    
    pcm_val += 0x84;
    int exponent = 7;
    for (int expMask = 0x4000; (pcm_val & expMask) == 0 && exponent > 0; expMask >>= 1) {
        exponent--;
    }
    int mantissa = (pcm_val >> (exponent + 3)) & 0x0F;
    return ~(sign | (exponent << 4) | mantissa);
}

void setupI2S()
{
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT, // STEREO
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 64,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_SCK,
        .ws_io_num = I2S_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_SD
    };

    i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_PORT, &pin_config);
    i2s_zero_dma_buffer(I2S_PORT);
    i2s_start(I2S_PORT);
}

void setup()
{
    Serial.begin(SERIAL_BAUD);
    setupI2S();
}

void loop()
{
    size_t bytesRead = 0;
    i2s_read(I2S_PORT, samples, sizeof(samples), &bytesRead, portMAX_DELAY);

    int samplesRead = bytesRead / sizeof(int32_t);
    if (samplesRead == 0) return;

    for (int i = 0; i < samplesRead; i++)
    {
        // 1. Get standard 16-bit signed sample
        int16_t pcm16 = (int16_t)(samples[i] >> SAMPLE_SHIFT);
        
        // 2. Compress to 8-bit using mu-law and store it
        ulawBuf[i] = encode_ulaw(pcm16);
    }

    // Write the compressed 8-bit stream over the safe 460800 baud connection!
    Serial.write(ulawBuf, samplesRead);
}