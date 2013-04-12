( function( $ ) {

    var methods = {
        init: function(){

            //Get a handle on the container
            var container = this;

            //Refresh the dataset list
            container.ml_survey_your_datasets('refresh_dataset_list');

            //Get a handle on the add-datasets-button
            var add_dataset_button = container.find('#add-dataset-button');

            //Add the on click handler to the button
            add_dataset_button.click(function(){

                container.ml_survey_your_datasets('close_dropdown');

                //Init the dataset manager
                $('#add-new-dataset').ml_survey_add_data_set();
            })
        },
        refresh_dataset_list: function() {
            //Get a handle on the container
            var container = this;

            //Load any existing datasets from the api
            container.find('#dataset-list').load('/your_datasets', function(){

                container.find('.remove-dataset-button')
                    .click(function(e){

                        var dataset  = $(this).parents('.dataset');

                        var dataset_id = dataset.data('dataset_id');

                        dataset.slideUp(function() { dataset.remove(); });

                        $.get('/dataset/remove/' + dataset_id);

                        return false;
                    });

                container.find('.dataset')
                    .click(function(){

                        container.ml_survey_your_datasets('close_dropdown');

                        var dataset = $(this);

                        var dataset_id = dataset.data('dataset_id');

                        $('#page-body').ml_survey({ dataset_id: dataset_id });
                    })

                    .mouseenter(function() {

                        $(this).addClass('ui-state-highlight');
                        $(this).find('.remove-dataset-button').fadeIn();
                    })

                    .bindWithDelay('mouseleave', function() {

                        $(this).removeClass('ui-state-highlight');
                        $(this).find('.remove-dataset-button').fadeOut();
                    }, 100)
            });
        },
        close_dropdown: function() {
            $('#your-datasets').parents('.dropdown:first').find('.dropdown-toggle:first').click();
        }
    };

    $.fn.ml_survey_your_datasets = function ( method ) {
        if ( methods[method] ) return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        else if ( typeof method === 'object' || ! method ) return methods.init.apply( this, arguments );
        else $.error( 'Method ' +  method + ' does not exist on jQuery.ml_survey_your_datasets' );
    }

})( jQuery );
