#include <Arduino.h>
#include <driver/i2s.h>
#include <stdlib.h>

#define I2S_WS   25
#define I2S_SCK  26
#define I2S_SD   39
#define I2S_PORT I2S_NUM_0

#define SAMPLE_RATE  16000
#define BUFFER_LEN   256
#define SERIAL_BAUD  921600

// INMP441 outputs 24-bit audio left-justified in a 32-bit I2S slot.
#define SAMPLE_SHIFT 14

int32_t samples[BUFFER_LEN];
int16_t pcmBuf[BUFFER_LEN / 2];

static int32_t pickActiveSample(int32_t left, int32_t right)
{
    int32_t l = abs(left);
    int32_t r = abs(right);
    return (l >= r) ? left : right;
}

void setupI2S()
{
    i2s_config_t i2s_config =
    {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
        // Read both slots; ESP-IDF often swaps L/R vs INMP441 L/R pin wiring.
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 64,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };

    i2s_pin_config_t pin_config =
    {
        .bck_io_num = I2S_SCK,
        .ws_io_num = I2S_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_SD
    };

    i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_PORT, &pin_config);
    i2s_zero_dma_buffer(I2S_PORT);
    i2s_start(I2S_PORT);

    // Discard startup buffers while the mic stabilizes.
    for (int i = 0; i < 8; i++)
    {
        size_t bytesRead = 0;
        i2s_read(I2S_PORT, samples, sizeof(samples), &bytesRead, portMAX_DELAY);
    }
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

    int samplesRead = bytesRead / (int)sizeof(int32_t);
    int frames = samplesRead / 2;
    if (frames == 0)
        return;

    for (int i = 0; i < frames; i++)
    {
        int32_t raw = pickActiveSample(samples[i * 2], samples[i * 2 + 1]);
        pcmBuf[i] = (int16_t)(raw >> SAMPLE_SHIFT);
    }

    Serial.write((uint8_t *)pcmBuf, frames * sizeof(int16_t));
}
