( function( $ ) {

    var methods = {
        refresh_data: function(data) {

            //Get a handle on the container
            var container = this;

            //Get the dataset id
            var dataset_id = data.dataset_id;

            if (data == null || dataset_id == null)
                container.load('/survey/html/empty_capture');
            else
                container.load('/survey/capture/' + dataset_id, function(){

                    container.find('#download-button').click(function(){

                        //Close this drop down menu
                        $(this).parents('.dropdown:first').find('.dropdown-toggle').click();
                    })
                })
        },
        empty: function() {

            //Get a handle on the container
            var container = this;

            container.load('/survey/html/empty_capture');
        }
    };

    $.fn.ml_survey_capture = function ( method ) {
        if ( methods[method] ) return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        else if ( typeof method === 'object' || ! method ) return methods.init.apply( this, arguments );
        else $.error( 'Method ' +  method + ' does not exist on jQuery.ml_survey_capture' );
    }

})( jQuery );
