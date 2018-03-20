
from artiq.language.core import kernel, delay, portable
from artiq.language.units import ns

from artiq.coredevice import spi2 as spi


ADC_SPI_CONFIG = (0*spi.SPI_OFFLINE | 0*spi.SPI_END |
        1*spi.SPI_INPUT | 0*spi.SPI_CS_POLARITY |
        0*spi.SPI_CLK_POLARITY | 0*spi.SPI_CLK_PHASE |
        0*spi.SPI_LSB_FIRST | 0*spi.SPI_HALF_DUPLEX)

PGIA_SPI_CONFIG = (0*spi.SPI_OFFLINE | 1*spi.SPI_END |
        0*spi.SPI_INPUT | 0*spi.SPI_CS_POLARITY |
        0*spi.SPI_CLK_POLARITY | 0*spi.SPI_CLK_PHASE |
        0*spi.SPI_LSB_FIRST | 0*spi.SPI_HALF_DUPLEX)


@portable
def adc_value(data):
    """Convert a ADC result packet to SI units (Volt)"""
    return ...


class Sampler:
    """Sampler 16-bit, 8-channel simultaneous-sampling ADC with 
    programmable-gain front end.

    :param adc_spi_device: ADC SPI bus device name
    :param cnv_device: CNV RTIO TTLOut channel name
    :param sdr_mode_device: SDR mode TTLOut channel name
    :param pgia_spi_device: Programmable-gain instrumentation amplifier (PGIA) 
        SPI bus device name
    :param div: SPI clock divider both busses (default: 2)
    :param core_device: Core device name
    """
    #kernel_invariants = {"bus", "core", "conv", "div"}

    def __init__(self, dmgr, adc_spi_device, cnv_device, sdr_mode_device,
                 pgia_spi_device, div=2, core_device="core"):        
        self.adc_bus = dmgr.get(adc_spi_device)
        self.pgia_bus = dmgr.get(pgia_spi_device)
        self.sdr_mode = dmgr.get(sdr_mode_device)
        self.cnv = dmgr.get(cnv_device)
        self.core = dmgr.get(core_device)

        self.div = div
        self.gains=0x0000
        #self.v_ref=5.

    @kernel
    def init(self):
        self.sdr_mode.output(0)

    @kernel
    def set_gain_mu(self, channel, gain):
        """Set instrumentation amplifier gain for a channel.

        The four gain settings (0, 1, 2, 3) corresponds to gains of
        (1, 10, 100, 1000) respectively.

        :param channel: Channel index
        :param gain: Gain setting
        """
        self.gains &= ~(0b11 << (channel*2))
        self.gains |= gain << (channel*2)
        self.pgia_bus.set_config_mu(PGIA_SPI_CONFIG, 16, self.div, 1)
        self.pgia_bus.write(self.gains)
        return self.pgia_bus.read()

    # @kernel
    # def init(self, data):
    #     """Set up the ADC sequencer.

    #     :param data: List of 8 bit control words to write into the sequencer
    #         table.
    #     """
    #     if len(data) > 1:
    #         self.bus.set_config_mu(SPI_CONFIG,
    #                                8, self.div, SPI_CS_ADC)
    #         for i in range(len(data) - 1):
    #             self.bus.write(data[i] << 24)
    #     self.bus.set_config_mu(SPI_CONFIG | spi.SPI_END,
    #                            8, self.div, SPI_CS_ADC)
    #     self.bus.write(data[len(data) - 1] << 24)

    @portable
    def pos(self, data):
        #Check if the voltage is positive or negative
        return((data & 0xa000) >> 15)


    @portable
    def convert(self, data):
        """Convert a ADC result packet to SI units (Volt)"""


    @kernel
    def sample_mu(self, channel):
        """Acquire a sample:

        Perform a conversion and transfer the sample.

        :param next_ctrl: ADC control word for the next sample
        :return: The ADC result packet (machine units)
        """
        self.cnv.pulse(30*ns)  # t_CNVH
        delay(450*ns)  # t_CNV
        self.adc_bus.set_config_mu(ADC_SPI_CONFIG | spi.SPI_END, 16, 
                                    self.div, 1)
        return [self.bus.read() for _ in range(last_ch)]

    def sample_channel_mu(self, channel=7):
        """ """
        ch = 6 - channel
        return sample_mu(ch)


    @kernel
    def sample(self, next_ctrl=0):
        """Acquire a sample

        .. seealso:: :meth:`sample_mu`

        :param next_ctrl: ADC control word for the next sample
        :return: The ADC result packet (Volt)
        """
        return adc_value(self.sample_mu())

    # @kernel
    # def burst_mu(self, data, dt_mu, ctrl=0):
    #     """Acquire a burst of samples.

    #     If the burst is too long and the sample rate too high, there will be
    #     RTIO input overflows.

    #     High sample rates lead to gain errors since the impedance between the
    #     instrumentation amplifier and the ADC is high.

    #     :param data: List of data values to write result packets into.
    #         In machine units.
    #     :param dt: Sample interval in machine units.
    #     :param ctrl: ADC control word to write during each result packet
    #         transfer.
    #     """
    #     self.bus.set_config_mu(SPI_CONFIG | spi.SPI_INPUT | spi.SPI_END,
    #                            24, self.div, SPI_CS_ADC)
    #     for i in range(len(data)):
    #         t0 = now_mu()
    #         self.conv.pulse(40*ns)  # t_CNVH
    #         delay(560*ns)  # t_CONV max
    #         self.bus.write(ctrl << 24)
    #         at_mu(t0 + dt_mu)
    #     for i in range(len(data)):
    #         data[i] = self.bus.read()
