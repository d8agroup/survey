( function( $ ) {

    var methods = {
        init: function(){

            //Get a handel on the login container
            var container = this;

            //Get the form submit button
            var submit_button = container.find('#login-button');

            //Attache the keyup handler to check for enter signals
            container.keyup(function(e){

                //Only stop on enter (13)
                if (e.keyCode == 13){

                    //Prevent the default action
                    e.preventDefault();

                    //Call the submit button.click
                    submit_button.click();
                }
            });

                //Attach the click handler
            submit_button.click(function(){

                //Get the submit button
                var submit_button = $(this);

                //Get the form
                var form = submit_button.parents('form:first');

                //Remove any existing errors
                form.find('.errors').remove();

                //Get the serialized form data
                var form_data = form.serialize();

                //Get the form action
                var action = form.attr('action');

                //Make the request to the server
                $.post(action, form_data, function(return_data){

                    //Get the login status
                    var status = return_data.status;

                    //If there were errors
                    if (status == 'error') {

                        //Get a jQuery handle on the error template
                        var error_template = return_data.error_template;

                        form.prepend(error_template);
                    }
                    else {

                        //Redirect to the home page
                        document.location = "/home";
                    }
                });

            });
        }
    };

    $.fn.ml_survey_login = function ( method ) {
        if ( methods[method] ) return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        else if ( typeof method === 'object' || ! method ) return methods.init.apply( this, arguments );
        else $.error( 'Method ' +  method + ' does not exist on jQuery.ml_survey_login' );
    }

})( jQuery );
