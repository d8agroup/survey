(function($){
    $.fn.ml_survey_question = function(){
        var question = this;

        question
            .mouseenter(function(){
                $(this).addClass('hover');
            })

            .mouseleave(function(){
                $(this).removeClass('hover');
            })

            .draggable({
                revert:true,
                helper:"clone"
            });

        return question;
    }
})(jQuery);