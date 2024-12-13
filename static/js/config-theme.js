/* --------------------------------------------------------------------------

 * Copyright 2020 All Rights Reserved.
 * -------------------------------------------------------------------------- 
 * javascript handle initialization
    1. Slideshow
    2. Counter
    3. Mobile nav button
    4. Tradingview widget
    5. Isotope filter
 * -------------------------------------------------------------------------- */

'use strict';

const HomepageApp = {
    //----------- 1. Slideshow -----------
    theme_slideshow: function() {
        new CarouselConfig({
            fadeTransition: false,
            darkMode: true,
            interval: 6000,
            control: {
                hide: true,
                onHover: false
            },
            indicators: {
                hide: false,
                onHover: false
            },
            height: {
                desktop: '570px',
                tablet: '436px',
                phone: '360px'
            }
        }).init();
    },
    //---------- 2. Counter -----------
    theme_counter: function() {
        new CounterUp({
            selector: '.count',
            start: 0,
            duration: 3200,
            intvalues: true,
            interval: 50
        }).start()
    },
    //---------- 3. Mobile nav button -----------
    theme_mobilenav: function() {
        new MobileNavbar({
            addonButtons: true, // options to use addon buttons, set it "false" if you won't use addon buttons
            buttons: [{
                name: 'Login', // button name
                url: 'https://www.bontren.com/member/user/login', // button url
                type: 'primary', // button type (default, primary, secondary, danger, text)
                icon: 'sign-in-alt' // button icon, you can use all icons from here : https://fontawesome.com/icons?d=gallery&s=solid&m=free
            }, ]
        }).init();
    },
    //---------- 4. Tradingview widget -----------
    theme_tradingview: function() {
        if (window.tradingWidget)
            tradingWidget({
                widget: [{
                        type: "market-overview",
                        theme: "light",
                        symbol: [ // array of instruments symbol based on Tradingview
                            {
                                s: "FX:EURUSD"
                            },
                            {
                                s: "FX:GBPUSD"
                            },
                            {
                                s: "FX:USDJPY"
                            },
                            {
                                s: "FX:USDCHF"
                            },
                            {
                                s: "FX:AUDUSD"
                            },
                            {
                                s: "FX:USDCAD"
                            }
                        ]
                    },
                    {
                        type: "symbol-overview",
                        theme: "light",
                        symbol: "GOOGL" // symbol based on Tradingview
                    }
                ]
            });
    },
    //---------- 5. Isotope filter -----------
    theme_isotope: function() {
        const isoWrapper = document.querySelectorAll('.isotope-wrapper')
        const isoFilter = document.querySelectorAll('.isotope-filter')

        isoWrapper.forEach((elem, index) => {
            const isotope = new Isotope(elem, {
                animationOptions: {
                    duration: 750,
                    easing: 'linear',
                    queue: false
                }
            })
            isoFilter[index].addEventListener('click', e => {
                isotope.arrange({
                    filter: e.target.getAttribute('data-filter')
                })
            })
        });
    },
    theme_init: function() {
        HomepageApp.theme_slideshow();
        HomepageApp.theme_counter();
        HomepageApp.theme_mobilenav();
        HomepageApp.theme_tradingview();
        HomepageApp.theme_isotope();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    HomepageApp.theme_init();
});