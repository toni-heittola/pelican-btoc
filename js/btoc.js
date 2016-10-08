
!function ($) {
  $(function(){

    var $window = $(window)
    var $body   = $(document.body)
    var navHeight = $('.navbar').outerHeight(true) + 10

    $body.scrollspy({
      target: '.btoc-container',
      offset: navHeight
    })

    $window.on('load', function () {
      $body.scrollspy('refresh')
    })

    setTimeout(function () {
      $('.btoc-container').affix({
        offset: {
          top: function () {
            var offsetTop = $('.btoc-container').offset().top
            return (this.top = offsetTop)
          }
        , bottom: function () {
            return (this.bottom = $('.footer').outerHeight(true))
          }
        }
      })
    }, 100)

    /*
    setTimeout(function () {
      $('.bs-top').affix()
    }, 100)

    $('.bs-docs-navbar').tooltip({
      selector: "a[data-toggle=tooltip]",
      container: ".bs-docs-navbar .nav"
    })

    $('.bs-docs-container [href=#]').click(function (e) {
      e.preventDefault()
    })
    */
  })

}(window.jQuery)
