( function( $ ) {

    var methods = {
        init: function(data){

            //Get a handle on the container
            var container = this;

            var dataset_id = data.dataset_id;

            var dataset_name = data.dataset_name;

            $('#dataset-name').html('<i class="icon-angle-right"></i> ' + dataset_name);

            container.data('dataset_id', dataset_id);

            container.data('dataset_name', dataset_name);

            container.load('/survey/' + dataset_id, function(){

                container.find('.question').each(function(){
                    $(this).ml_survey_question();
                });

                container.find('#chart-area-one').ml_survey_chartarea();
                if (data.configuration != null && data.configuration.chart_area_one != null)
                    container.find('#chart-area-one').ml_survey_chartarea(
                        'build_from_data',
                        data.configuration.chart_area_one
                    );
         
                container.find('#chart-area-two').ml_survey_chartarea();
                if (data.configuration != null && data.configuration.chart_area_two != null)
                    container.find('#chart-area-two').ml_survey_chartarea(
                        'build_from_data',
                        data.configuration.chart_area_two
                    );

                $('#rewind-container').ml_survey_rewind({dataset_id: dataset_id});
                $('#capture-container').ml_survey_capture('refresh_data', {dataset_id: dataset_id});
            });
        },
        record_activity: function() {

            var container = this;

            var post_data = {
                dataset_id: container.data('dataset_id'),
                configuration: {
                    dataset_id: container.data('dataset_id'),
                    dataset_name: container.data('dataset_name'),
                    chart_area_one: $('#chart-area-one').ml_survey_chartarea('return_data'),
                    chart_area_two: $('#chart-area-two').ml_survey_chartarea('return_data')
                }
            };

            $.ajax('/survey/record_activity', {
                data: JSON.stringify(post_data),
                contentType: "application/json",
                method: "POST",
                complete: function() {
                    $('#rewind-container').ml_survey_rewind('refresh_data');
                    $('#capture-container').ml_survey_capture('refresh_data', { dataset_id: container.data('dataset_id') })
                }
            });
        }
    };

    $.fn.ml_survey = function ( method ) {
        if ( methods[method] ) return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        else if ( typeof method === 'object' || ! method ) return methods.init.apply( this, arguments );
        else $.error( 'Method ' +  method + ' does not exist on jQuery.ml_survey' );
    }

})( jQuery );
