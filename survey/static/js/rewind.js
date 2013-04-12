( function( $ ) {

    var methods = {
        init: function(data){

            //Get a handle on the container
            var container = this;

            //Store the current dataset id
            container.data('dataset_id', data.dataset_id);

            container.ml_survey_rewind('refresh_data');

            container.parent().find('.dropdown-toggle').click(function(){
                setTimeout(function(){
                    if ($('#rewind-list').scrollLeft() == 0)
                        $('#rewind-list').scrollLeft(1000);
                }, 50);
            })

            //Return the container
            return container;
        },
        refresh_data: function() {

            //Get a handle on the container
            var container = this;

            //Get the dataset id
            var dataset_id = container.data('dataset_id');

            $.get('/survey/get_activity/' + dataset_id + '/20', function(template){

                //Get a handel on the list container
                var rewind_list = $('#rewind-list');

                //Add the template to the list
                rewind_list.html(template);

                rewind_list.find('img')

                    .bindWithDelay('mouseenter', function() {
                        $(this).parent().find('.activity-details').slideDown();
                    }, 200)

                    .bindWithDelay('mouseleave', function(){
                        $(this).parent().find('.activity-details').slideUp();
                    }, 700)

                    .click(function() {

                        //Get the activity id
                        var activity = $(this).data('activity');

                        //Re init the survey
                        $('#page-body').ml_survey(activity);

                        //Close this drop down menu
                        $(this).parents('.dropdown:first').find('.dropdown-toggle').click();
                    })
            });
        },
        empty: function() {

            //Get a handel on the list container
            var rewind_list = $('#rewind-list');

            rewind_list.load('/survey/html/empty_rewind');
        }
    };

    $.fn.ml_survey_rewind = function ( method ) {
        if ( methods[method] ) return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        else if ( typeof method === 'object' || ! method ) return methods.init.apply( this, arguments );
        else $.error( 'Method ' +  method + ' does not exist on jQuery.ml_survey_rewind' );
    }

})( jQuery );
