( function( $ ) {

    var methods = {
        init: function() {

            //Get a handle on the container
            var container = this;

            container.load('/add_dataset', function(){

                container.find('.step').hide();
                container.find('#step-intro').show();

                container.data('state', 'init');

                if (container.data('uiDialog') != null)
                    container.dialog('open');
                else
                    container.dialog({
                        modal: true,
                        resizable: false,
                        draggable: false,
                        width: $(window).width() - 300,
                        height: $(window).height() - 150
                    });

                container.find('.content').css('height', container.height() - 70);

                //attach a handler to the cancel upload button
                container.find('#cancel-upload-button').click(function(){

                    $(this).parents('.modal-container:first').dialog('close');
                });

                //Create a new gui
                var file_id = guid();

                //Attach it to the outer container
                container.data('file_id', file_id);

                //Create the new Ajax Uploader
                new AjaxUpload('upload-dataset', {
                    action: '/add_dataset/upload_file',
                    data: { file_id: file_id },
                    name: 'data_upload',
                    onSubmit: function(file, extensions){

                        container.find('#upload-dataset i')
                            .attr('class', '')
                            .addClass('icon-spin')
                            .addClass('icon-spinner');

                        container.find('#upload-dataset')
                            .addClass('disabled');
                    },
                    onComplete:function(file, response){
                        container.ml_survey_add_data_set('render_processing_upload');
                    }
                });
            })
        },
        render_processing_upload: function() {

            var container = this;

            container.data('state', 'render_processing_upload');

            container.find('.step').hide();
            container.find('#step-processing-upload').show();

            container.find('#finished-processing-button').click(function(){
                container.ml_survey_add_data_set('render_processing_upload_complete');
            });

            var file_id = container.data('file_id');

            var display_progress_function = function(file_id) {

                if (container.data('state') != 'render_processing_upload' || container.data('file_id') != file_id)
                    return;

                $.getJSON('/add_dataset/upload_file_progress/' + file_id, function(return_data){

                    if (return_data.status == "error")
                        return container.ml_survey_add_data_set('render_error', { error_template: return_data.error_template});

                    var progress = return_data.progress;

                    var progress_messages = container.find('#processing-messages li');

                    var progress_percent = parseInt((progress / progress_messages.length) * 100);

                    container.find('#upload-progressbar .ui-progressbar-value').animate({ 'width': progress_percent + "%"});

                    $.each(progress_messages, function(index, item){
                        var icon = $(item).find('i');
                        icon.attr('class', '');
                        if (index < progress)
                            icon.addClass('icon-check');
                        if (index == progress)
                            icon.addClass('icon-spin').addClass('icon-spinner');
                        if (index > progress)
                            icon.addClass('icon-icon-check-empty');
                    });

                    if (progress < progress_messages.length)
                        return setTimeout(function(){ display_progress_function(file_id); }, 500);

                    container.find('#finished-processing').slideDown();
                })
            };

            setTimeout(function(){
                display_progress_function(file_id);
            }, 500)
        },
        render_processing_upload_complete: function() {
            var container = this;

            container.data('state', 'render_processing_upload_complete');

            container.find('.step').hide();
            container.find('#step-processing-upload-complete').show();

            var file_id = container.data('file_id');

            container.find('#metadata-form-container').load('/add_dataset/edit_metadata/' + file_id, function(){

            });

            container.find('#finished-add-dataset-button').click(function(){

                var button = $(this);

                var form = button.parents('.step:first').find('form:first');

                var form_data = form.serialize();

                $.post('/add_dataset/edit_metadata/' + file_id, form_data, function(return_data){

                    $('#your-datasets').ml_survey_your_datasets('refresh_dataset_list');

                    $('#page-body').ml_survey(return_data);
                });

                button.parents('.modal-container:first').dialog('close');
            })
        },
        render_error: function(data) {
            var container = this;

            container.data('state', 'error');
            container.data('file_id', null);

            container.find('.step').hide();
            container.find('#step-error').show();

            container.find('#step-error .error-container').html(data.error_template);

            container.find('#retry-button').click(function(){
                container.ml_survey_add_data_set();
            });

            return container;
        }
    };

    $.fn.ml_survey_add_data_set = function ( method ) {
        if ( methods[method] ) return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        else if ( typeof method === 'object' || ! method ) return methods.init.apply( this, arguments );
        else $.error( 'Method ' +  method + ' does not exist on jQuery.ml_survey_add_data_set' );
    }

})( jQuery );
