(function($){
    var methods = {
        init:function(){
            var filters = this;
            filters.ml_survey_filters('apply_question_droppable');
            filters.find('.close_button').each(function(){
                $(this).click(function(){
                    var filter_container = $(this).parents('.filter-container');
                    filter_container.removeData();
                    filter_container.parents('.chart-area-container').ml_survey_chartarea('repaint');
                });
            });
            return filters;
        },
        apply_question_droppable:function(){
            var filters = this;
            filters.find('.filter-container').droppable({
                accept:'.question',
                activeClass:'drop-active',
                drop:function(event, ui){
                    var droppable = $(this);
                    var draggable = ui.draggable;
                    var facet_name = draggable.data('facet_name');
                    var display_name = draggable.data('display_name');
                    droppable.data('facet_name', facet_name);
                    droppable.data('display_name', display_name);
                    $(this).parents('.chart-area-container').ml_survey_chartarea('repaint');
                }
            });
            return filters;
        },
        update_filters:function(data){
            var filters_data = data.filters;
            var chart_area_id = data.chart_area_id;
            var filters = this;
            var question_containers = filters.find('.filter-container');
            for (var facet_name in filters_data) {
                for (var x=0; x<question_containers.length; x++){
                    var filter_container = $(question_containers[x]);
                    if (filter_container.data('facet_name') == facet_name) {
                        var id = guid();
                        filter_container.attr('id', 'filter_' + id);
                        filter_container.find('.title').html(filters_data[facet_name].key);
                        filter_container.addClass('in-use');

                        var seriesDefaults = {};
                        if (filters_data[facet_name].is_selected){
                            seriesDefaults = {
                                renderer: jQuery.jqplot.DonutRenderer,
                                rendererOptions: {
                                    sliceMargin:4,
                                    showDataLabels: true,
                                    dataLabels:'label'
                                },
                                highlighter: {
                                    show: false,
                                    formatString:'',
                                    tooltipLocation:'s',
                                    useAxesFormatters:false
                                }
                            }
                        }
                        else {
                            seriesDefaults = {
                                renderer: jQuery.jqplot.DonutRenderer,
                                rendererOptions: {
                                    sliceMargin:4,
                                    showDataLabels: false
                                },
                                highlighter: {
                                    show: true,
                                    formatString:'%s',
                                    tooltipLocation:'s',
                                    useAxesFormatters:false
                                }
                            }
                        }

                        var chart = jQuery.jqplot(
                            'filter_' + id + ' .chart-container',
                            [filters_data[facet_name].values],
                            {
                                title: ' ',
                                legend: { show:false },
                                seriesDefaults: seriesDefaults,
                                seriesColors:filters_data[facet_name].colors,
                                grid:{
                                    background:'#1D2228',
                                    borderWidth:0,
                                    shadow:false
                                }
                            }
                        );

                        charts[chart_area_id].push(chart);


                        $('#filter_' + id + ' .chart-container').unbind();
                        if (filters_data[facet_name].is_selected){
                            $('#filter_' + id + ' .chart-container').bind('jqplotDataClick',
                                function (ev, seriesIndex, pointIndex, data) {
                                    $(ev.target).parents('.filter-container').data('facet_value', '');
                                    $(ev.target).parents('.chart-area-container').ml_survey_chartarea('repaint');
                                }
                            );
                        }
                        else {
                            $('#filter_' + id + ' .chart-container').bind(
                                'jqplotDataClick',
                                function (ev, seriesIndex, pointIndex, data) {
                                    $(ev.target).parents('.filter-container').data('facet_value', data[0]);
                                    $(ev.target).parents('.chart-area-container').ml_survey_chartarea('repaint');
                                }
                            );
                        }
                    }
                }

            }
            return this;
        },
        clear: function() {

            //Get a handle on the container
            var container = this;

            //Reload the filter list html
            container.find('.filters-list').load('/survey/html/filters_list', function(){

                //Call the filters init function
                container.ml_survey_filters();
            });
        }
    };

    $.fn.ml_survey_filters = function( method )
    {
        if ( methods[method] ) return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        else if ( typeof method === 'object' || ! method ) return methods.init.apply( this, arguments );
        else $.error( 'Method ' +  method + ' does not exist on jQuery.ml_survey_filters' );
    }
})(jQuery);