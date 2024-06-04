!function ($) {
  $(function(){
    $(document).ready(function() {
        if($('.btoc-container').hasClass('sticky-top')){
            $('.btoc-container').css('top', $('#topmenu').height() + 10);
            $(window).resize(function(){
                $('.btoc-container').css('top', $('#topmenu').height() + 10);
            });
        }

        $('.btoc-nav').each(function(){
            var toc_levels = $(this).data('toc-levels');

            tocbot.init({
              tocElement    : this,                 // Where to render the table of contents.
              contentSelector: 'section.body',      // Where to grab the headings to build the table of contents.
              headingSelector: toc_levels,          // Which headings to grab inside of the contentSelector element.
              collapseDepth  :  0,
              orderedList    :  false,              // orderedList can be set to false to generate unordered lists (ul)
                                                    // instead of ordered lists (ol)

              hasInnerContainers: false,            // For headings inside relative or absolute positioned containers within content.
              ignoreSelector: '.toc-skip',          // Headings that match the ignoreSelector will be skipped.

              headingsOffset: 0,
              scrollSmooth: false,
              scrollSmoothOffset: 0,
              scrollSmoothDuration: 420,
              throttleTimeout: 50,
            });
        });

        $('a.toc-link').on('click', function(){
            //Remove any previously added classes of 'clicked' to all toc-link elements
            $('a.toc-link').removeClass('clicked');
            //Add the class to the currently clicked anchor tag
            $(this).addClass('clicked');
        });
    });
  })
}(window.jQuery)