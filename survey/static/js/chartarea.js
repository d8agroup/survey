(function($){
    var methods = {
        init:function(data){

            var chart_area = this;

            chart_area.data('dataset_id', data.dataset_id);

            chart_area.find('.filters').ml_survey_filters();

            chart_area.ml_survey_chartarea('apply_question_droppable');

            chart_area.find('.remove-chart-button').click(function(){

                $(this).parents('.chart-area-container').ml_survey_chartarea('clear');
            });

            return chart_area;
        },
        repaint:function(skip_record_activity){

            var chart_area = this;

            if (chart_area.find('.question-container .title').length == 0){

                chart_area.removeClass('has-data');

                chart_area.find('.filters').ml_survey_filters('clear');
            }
            else {

                chart_area.addClass('has-data');

                var question_containers = chart_area.find('.question-container');

                var questions = [];

                for (var x=0; x<question_containers.length; x++) {

                    var facet_name = $(question_containers[x]).data('facet_name');

                    var display_name = $(question_containers[x]).data('display_name');

                    if (display_name == null || facet_name == null)
                        continue;

                    questions[questions.length] = {
                        facet_name:facet_name,
                        display_name:display_name
                    }
                }

                var filter_container = chart_area.find('.filter-container');
                var filters = [];
                for (var x=0; x<filter_container.length; x++) {
                    var facet_name = $(filter_container[x]).data('facet_name');
                    var display_name = $(filter_container[x]).data('display_name');
                    var facet_value = $(filter_container[x]).data('facet_value');
                    if (display_name == null || facet_name == null)
                        continue;
                    filters[filters.length] = {
                        facet_name:facet_name,
                        display_name:display_name,
                        facet_value:facet_value
                    }
                }

                var search_data = JSON.stringify({questions:questions, filters:filters});

                var post_data = {
                    search_data:search_data,
                    chart_area_id:chart_area.attr('id'),
                    dataset_id: chart_area.data('dataset_id')
                };

                $.post('/survey/get_graph_data', post_data, function(data){

                    for(var x=0; x<charts[data.chart_area_id].length; x++)
                        charts[data.chart_area_id][x].destroy();


                    $('#' + data.chart_area_id + ' .filters').ml_survey_filters('update_filters', { filters:data.filters, chart_area_id:data.chart_area_id});

                    if (data.graph_type == 'pie') {

                        var chart = jQuery.jqplot(
                            data.chart_area_id + ' .chart',
                            [data.graph_data.values],
                            {
                                title: ' ',
                                legend: { show:false },
                                seriesDefaults: {
                                    renderer: jQuery.jqplot.DonutRenderer,
                                    rendererOptions: {
                                        dataLabelThreshold: 0.1,
                                        sliceMargin:1,
                                        showDataLabels: true,
                                        dataLabels:data.graph_data.labels
                                    }
//                                    highlighter: {
//                                        show: false,
////                                        formatString:'%s',
//                                        tooltipLocation:'s',
//                                        useAxesFormatters:false
//                                    }
                                },
                                seriesColors:data.graph_colors,
                                grid:{
                                    background:'#1D2228',
                                    borderWidth:0,
                                    shadow:false
                                }
                            }

                        );
                        charts[data.chart_area_id].push(chart);
                    }

                    if (skip_record_activity == null || skip_record_activity == false)
                        $('#page-body').ml_survey('record_activity');
                });
            }
            return chart_area;
        },
        apply_question_droppable:function(){

            var chart_area = this;

            chart_area.find('.questions-and-chart').droppable({
                accept:'.question',
                activeClass:'drop-active',
                drop:function(event, ui){

                    var droppable = $(this).find('.question-container');

                    var draggable = ui.draggable;

                    var facet_name = draggable.data('facet_name');

                    var display_name = draggable.data('display_name');

                    var html = $("<p class='title'>"+display_name+"</p>");

                    droppable.html(html);

                    droppable.data('facet_name', facet_name);

                    droppable.data('display_name', display_name);

                    chart_area.ml_survey_chartarea('repaint');
                }
            });
            return chart_area;
        },
        clear:function(callback){

            var chart_area = this;

            chart_area.removeClass('has-data');

            chart_area.load('/survey/html/chart_area', function(){
                chart_area.ml_survey_chartarea({dataset_id: chart_area.data('dataset_id')});
                if (callback != null)
                    callback();
            });

            return chart_area;
        },
        return_data:function(){

            var chart_area = this;

            var question_container = chart_area.find('.question-container');

            var facet_name = question_container.data('facet_name');

            if (facet_name == null)
                return { is_empty: true };

            var main_question = {
                facet_name: facet_name,
                display_name: question_container.data('display_name'),
                chart: jqplotToImg(chart_area.find('.chart'))
            };

            var filters = [];

            var filter_containers = chart_area.find('.filter-container');

            for (var x=0; x<filter_containers.length; x++){
                var filter_container = $(filter_containers[x]);
                if (!filter_container.is('.in-use'))
                    filters.push({
                        is_empty: true
                    });
                else
                    filters.push({
                        is_empty: false,
                        facet_name: filter_container.data('facet_name'),
                        display_name: filter_container.data('display_name'),
                        facet_value: filter_container.data('facet_value'),
                        chart: jqplotToImg(filter_container.find('.chart-container'))
                    });
            }

            return {
                is_empty: false,
                main_question: main_question,
                filters:filters
            };
        },
        build_from_data:function(data){
            var chart_area = this;

            if (data != null && data.main_question != null && data.main_question.facet_name != null) {

                chart_area.ml_survey_chartarea('clear', function(){
                    chart_area.find('.question-container').data('facet_name', data.main_question.facet_name);
                    chart_area.find('.question-container').data('display_name', data.main_question.display_name);
                    chart_area.find('.question-container').html("<p class='title'>"+data.main_question.display_name+"</p>");
                    var filter_containers = chart_area.find('.filter-container');
                    for (var x=0; x<data.filters.length; x++){
                        $(filter_containers[x]).data('facet_name', data.filters[x].facet_name);
                        $(filter_containers[x]).data('facet_value', data.filters[x].facet_value);
                        $(filter_containers[x]).data('display_name', data.filters[x].display_name);
                    }
                    chart_area.ml_survey_chartarea('repaint', true);
                });
            }
            return chart_area;
        }
    };

    $.fn.ml_survey_chartarea = function( method ){
        if ( methods[method] ) return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        else if ( typeof method === 'object' || ! method ) return methods.init.apply( this, arguments );
        else $.error( 'Method ' +  method + ' does not exist on jQuery.ml_survey_chartarea' );
    }
})(jQuery);
